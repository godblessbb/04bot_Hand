import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# -------------------------------
# Text Encoder
# -------------------------------
class TextEmbedder(nn.Module):
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", output_dim=384, freeze=True):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.output_dim = output_dim
        if freeze:
            for p in self.model.parameters():
                p.requires_grad = False

    def forward(self, texts, device=None):
        if device is None:
            device = next(self.parameters()).device
        encoded = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        encoded = {k: v.to(device) for k, v in encoded.items()}
        with torch.no_grad():
            out = self.model(**encoded)
        embeddings = out.last_hidden_state.mean(dim=1)
        return embeddings  # [batch, output_dim]


# -------------------------------
# PointNet for object geometry
# -------------------------------
class PointNetEncoder(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64, output_dim=512, use_learnable_fallback=False):
        super().__init__()
        self.mlp1 = nn.Linear(input_dim, hidden_dim)
        self.mlp2 = nn.Linear(hidden_dim, output_dim)
        self.use_learnable_fallback = use_learnable_fallback

        if use_learnable_fallback:
            self.fallback_embedding = nn.Parameter(torch.zeros(output_dim))

    def forward(self, x):
        """
        x: [B, N_points, 3] or [N_points, 3]
           invalid points should be [inf, inf, inf]
        """
        added_batch = False
        if x.dim() == 2:  # [N_points, 3] → add batch dim
            x = x.unsqueeze(0)
            added_batch = True

        # mask invalid points
        valid_mask = ~torch.isinf(x).any(dim=-1)   # [B, N_points]

        # replace inf with 0 for safety
        x = torch.where(torch.isinf(x), torch.zeros_like(x), x)

        # feature extraction
        h = F.relu(self.mlp1(x))       # [B, N_points, hidden_dim]
        h = self.mlp2(h)               # [B, N_points, output_dim]

        # mask before pooling
        mask = valid_mask.unsqueeze(-1)   # [B, N_points, 1]
        h = h.masked_fill(~mask, float("-inf"))

        # global max pooling
        pooled, _ = h.max(dim=1)  # [B, output_dim]

        # handle "all invalid"
        all_invalid = ~valid_mask.any(dim=1)  # [B]
        if all_invalid.any():
            if self.use_learnable_fallback:
                pooled[all_invalid] = self.fallback_embedding
            else:
                pooled[all_invalid] = 0.0

        if added_batch:
            pooled = pooled.squeeze(0)  # back to [output_dim]

        return pooled

# -------------------------------
# Robot Policy
# -------------------------------
class RobotPolicy(nn.Module):
    def __init__(self, text_dim=384, model_dim=512, output_dim=25):
        super().__init__()
        self.model_dim = model_dim
        self.text_dim = text_dim

        # Action text embedder
        self.text_embedder = TextEmbedder(output_dim=text_dim)

        # Object embedder (text + geometry)
        self.pointnet = PointNetEncoder(output_dim=self.model_dim)

        # Quantitative state MLP
        # input: action_emb + object_emb + eef + fingers
        self.state_mlp = nn.Sequential(
            nn.Linear(2 * text_dim + self.model_dim + 25, self.model_dim),
            nn.ReLU(),
            nn.Linear(self.model_dim, self.model_dim),
            nn.ReLU(),
        )

        # Output head
        self.head = nn.Linear(self.model_dim, output_dim)

    def forward(self, batch):
        """
        batch: list of dicts from cvt_state_to_input
        Returns: [B,13] tensor
        """
        device = next(self.parameters()).device
        fused_list = []

        for item in batch:
            # Move tensors to device
            for key in ['obj_positions', 'eef_position', 'eef_orientation', 'finger_positions']:
                item[key] = item[key].to(device)

            # Action embedding
            action_emb = self.text_embedder([item['action']], device=device)  # [1, text_dim]

            # Object embeddings
            N = len(item['objects'])
            if N > 0:
                obj_text_emb = self.text_embedder(item['objects'], device=device)  # [N, text_dim]
                obj_geom_emb = torch.stack([self.pointnet(item['obj_positions'][j]) for j in range(N)])  # [N, model_dim]
                obj_emb_fused = torch.cat([obj_text_emb, obj_geom_emb], dim=-1)           # [N, model_dim]
                obj_emb_pooled = obj_emb_fused.mean(dim=0, keepdim=True)  # [1, model_dim + text_dim]
            else:
                obj_emb_pooled = torch.zeros(1, self.model_dim + self.text_dim, device=device)

            # Quantitative state: combine action, object, and numeric state
            state_vec = torch.cat([
                action_emb,           # [1, model_dim]
                obj_emb_pooled,       # [1, model_dim + text_dim]
                item['eef_position'].unsqueeze(0),    # [1,3]
                item['eef_orientation'].unsqueeze(0), # [1,6]
                item['finger_positions'].unsqueeze(0)   # [1,16]
            ], dim=-1)  # [1, 2*model_dim + 20]

            state_emb = self.state_mlp(state_vec)  # [1, model_dim]
            fused_list.append(state_emb.squeeze(0))

        out = torch.stack(fused_list, dim=0)  # [B, model_dim]
        out = self.head(out)                   # [model_dim, 6]
        return out

import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv

class GATModel(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, heads=8):
        super(GATModel, self).__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=heads)
        self.conv3 = GATConv(hidden_channels * heads, out_channels, heads=1)

    def forward(self, x, edge_index, edge_attr):
        x = F.elu(self.conv1(x, edge_index, edge_attr))
        x = F.dropout(x, p=0.6, training=self.training)
        x = F.elu(self.conv2(x, edge_index, edge_attr))
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv3(x, edge_index, edge_attr)
        return x

class LinkPredictor(torch.nn.Module):
    def __init__(self, in_channels):
        super(LinkPredictor, self).__init__()
        self.lin1 = torch.nn.Linear(in_channels * 2, 128)
        self.lin2 = torch.nn.Linear(128, 1)

    def forward(self, x_i, x_j):
        x = torch.cat([x_i, x_j], dim=-1)
        x = F.relu(self.lin1(x))
        return torch.sigmoid(self.lin2(x))

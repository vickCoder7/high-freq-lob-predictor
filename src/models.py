# pyrefly: ignore [missing-import]
import torch
# pyrefly: ignore [missing-import]
import torch.nn as nn

class LOBPredictor(nn.Module):
    """
    A 2-Layer LSTM network designed to predict high-frequency movements 
    in a Limit Order Book.
    """
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, num_classes: int, dropout: float = 0.2):
        """
        Args:
            input_size (int): Number of features per tick (e.g., spread, mid_price).
            hidden_size (int): Number of neurons in the LSTM hidden state.
            num_layers (int): Number of stacked LSTM layers.
            num_classes (int): Number of output classes (3 for UP, DOWN, STATIONARY).
            dropout (float): Dropout probability applied between LSTM layers.
        """
        super(LOBPredictor, self).__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size, 
            hidden_size=hidden_size,
            num_layers=num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.fc = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the neural network.
        
        Args:
            x (torch.Tensor): A batch of LOB sequences. Shape: (batch_size, seq_length, input_size)
            
        Returns:
            torch.Tensor: Logits for the 3 classes. Shape: (batch_size, num_classes)
        """
        # lstm_out shape: (batch_size, seq_length, hidden_size)
        # We ignore the hidden/cell state tuples for the next batch
        lstm_out, _ = self.lstm(x)
        
        # We only care about the prediction generated after observing the final tick
        # in the sequence. Slice the last time step.
        out = lstm_out[:, -1, :]
        
        # Pass through the fully connected layer to generate class logits
        logits = self.fc(out)
        
        return logits

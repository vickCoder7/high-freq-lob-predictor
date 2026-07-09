# pyrefly: ignore [missing-import]
import torch
import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
from torch.utils.data import Dataset
from typing import List

class LOBDataset(Dataset):
    """
    A PyTorch Dataset for High-Frequency Limit Order Book (LOB) data.
    
    Converts a flat Pandas DataFrame into sliding window sequences of length `seq_length`
    to feed into sequence models (like LSTM or Transformers).
    """
    def __init__(self, df: pd.DataFrame, feature_cols: List[str], target_col: str, seq_length: int = 50):
        """
        Args:
            df (pd.DataFrame): The dataframe containing LOB features and labels.
            feature_cols (List[str]): List of column names to be used as features.
            target_col (str): Column name representing the target label.
            seq_length (int): The number of past ticks to include in a single sequence.
        """
        self.seq_length = seq_length
        
        # Convert to numpy arrays for fast C-level slicing
        self.features = df[feature_cols].values.astype(np.float32)
        
        # Labels are natively -1 (DOWN), 0 (STATIONARY), 1 (UP).
        # PyTorch CrossEntropyLoss expects classes to be 0-indexed, positive integers.
        # Mapping: -1 -> 0, 0 -> 1, 1 -> 2
        self.labels = df[target_col].values.astype(np.int64) + 1
        
    def __len__(self) -> int:
        """
        The total number of sequences we can generate is the length of the dataset 
        minus the sequence length plus one.
        """
        return len(self.features) - self.seq_length + 1
    
    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Generates one sequence of features and its corresponding future label.
        
        Args:
            idx (int): The starting index of the sequence.
            
        Returns:
            Tuple of (features_sequence, target_label)
        """
        # Slice the sequence of features
        x = self.features[idx : idx + self.seq_length]
        
        # The label corresponds to the target value of the *last* tick in the sequence
        y = self.labels[idx + self.seq_length - 1]
        
        return torch.tensor(x), torch.tensor(y)

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCleaning:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.numerical_features = []
        self.categorical_features = []

    def identify_features(self):
        """Identify numerical and categorical features in the dataset."""
        self.numerical_features = self.data.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_features = self.data.select_dtypes(include=[object, 'category']).columns.tolist()
        logging.info(f"Numerical features: {self.numerical_features}")
        logging.info(f"Categorical features: {self.categorical_features}")

    def drop_duplicates(self):
        """Drop duplicate rows from the dataset."""
        initial_size = self.data.shape[0]
        self.data = self.data.drop_duplicates()
        final_size = self.data.shape[0]
        logging.info(f"Dropped {initial_size - final_size} duplicate rows.")

    def handle_missing_values(self, strategy: str = 'mean'):
        """Handle missing values in numerical columns."""
        logging.info("Handling missing values...")
        imputer = SimpleImputer(strategy=strategy)
        self.data[self.numerical_features] = imputer.fit_transform(self.data[self.numerical_features])
        missing_values_count = self.data.isnull().sum().sum()
        logging.info(f"Remaining missing values: {missing_values_count}")

    def handle_categorical_missing(self, strategy: str = 'most_frequent'):
        """Handle missing values in categorical columns."""
        logging.info("Handling missing values in categorical features...")
        imputer = SimpleImputer(strategy=strategy)
        self.data[self.categorical_features] = imputer.fit_transform(self.data[self.categorical_features])
        missing_values_count = self.data.isnull().sum().sum()
        logging.info(f"Remaining missing values in categorical features: {missing_values_count}")

    def remove_outliers(self, z_threshold: float = 3.0):
        """Remove outliers from numerical features based on Z-score."""
        logging.info(f"Removing outliers with Z-score threshold {z_threshold}...")
        for feature in self.numerical_features:
            mean, std = self.data[feature].mean(), self.data[feature].std()
            z_scores = (self.data[feature] - mean) / std
            outliers = np.abs(z_scores) > z_threshold
            self.data = self.data[~outliers]
        logging.info("Outliers removed.")

    def normalize_data(self, method: str = 'standard'):
        """Normalize the numerical features in the dataset."""
        logging.info(f"Normalizing data using {method} method...")
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        else:
            raise ValueError("Unsupported normalization method. Choose 'standard' or 'minmax'.")
        
        self.data[self.numerical_features] = scaler.fit_transform(self.data[self.numerical_features])

    def encode_categorical(self, encoding_type: str = 'onehot'):
        """Encode categorical features."""
        logging.info(f"Encoding categorical features using {encoding_type} encoding...")
        if encoding_type == 'onehot':
            self.data = pd.get_dummies(self.data, columns=self.categorical_features)
        elif encoding_type == 'label':
            for col in self.categorical_features:
                self.data[col] = self.data[col].astype('category').cat.codes
        else:
            raise ValueError("Unsupported encoding type. Choose 'onehot' or 'label'.")

    def detect_correlations(self, threshold: float = 0.9):
        """Detect highly correlated features."""
        logging.info("Detecting highly correlated features...")
        corr_matrix = self.data[self.numerical_features].corr().abs()
        upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        correlated_features = [column for column in upper_triangle.columns if any(upper_triangle[column] > threshold)]
        logging.info(f"Highly correlated features: {correlated_features}")
        return correlated_features

    def drop_highly_correlated(self, threshold: float = 0.9):
        """Drop highly correlated features from the dataset."""
        correlated_features = self.detect_correlations(threshold=threshold)
        self.data.drop(correlated_features, axis=1, inplace=True)
        self.numerical_features = [feature for feature in self.numerical_features if feature not in correlated_features]

    def summarize_data(self):
        """Print summary of the dataset after cleaning."""
        logging.info("Data summary after cleaning:")
        logging.info(f"Number of rows: {self.data.shape[0]}")
        logging.info(f"Number of columns: {self.data.shape[1]}")
        logging.info(f"Numerical features: {self.numerical_features}")
        logging.info(f"Categorical features: {self.categorical_features}")

    def export_cleaned_data(self, file_path: str):
        """Export cleaned data to a file."""
        logging.info(f"Exporting cleaned data to {file_path}...")
        self.data.to_csv(file_path, index=False)
        logging.info("Data exported successfully.")

if __name__ == "__main__":
    # Load dataset
    df = pd.read_csv("input_data.csv")

    # Initialize DataCleaning class
    cleaner = DataCleaning(df)
    
    # Perform cleaning steps
    cleaner.identify_features()
    cleaner.drop_duplicates()
    cleaner.handle_missing_values(strategy='mean')
    cleaner.handle_categorical_missing(strategy='most_frequent')
    cleaner.remove_outliers(z_threshold=3.0)
    cleaner.normalize_data(method='standard')
    cleaner.encode_categorical(encoding_type='onehot')
    cleaner.drop_highly_correlated(threshold=0.9)
    cleaner.summarize_data()
    
    # Export cleaned data
    cleaner.export_cleaned_data("cleaned_data.csv")
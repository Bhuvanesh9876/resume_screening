"""
Model Evaluation Module for Resume Screening System

This module provides tools to evaluate the accuracy of the resume screening model
by comparing predictions against ground truth labels.
"""

import json
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
import pandas as pd
from core.config import SHORTLIST_THRESHOLD


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    total_samples: int
    
    def to_dict(self) -> dict:
        return {
            'accuracy': round(self.accuracy, 4),
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'total_samples': self.total_samples
        }


class ModelEvaluator:
    """Evaluate resume screening model performance"""
    
    def __init__(self, ground_truth_file: str = "data/ground_truth.json"):
        """
        Initialize evaluator
        
        Args:
            ground_truth_file: Path to JSON file containing labeled data
        """
        self.ground_truth_file = ground_truth_file
        self.ground_truth = self._load_ground_truth()
    
    def _load_ground_truth(self) -> Dict[str, bool]:
        """
        Load ground truth labels from file
        
        Returns:
            Dictionary mapping resume names to boolean labels (True=shortlist, False=reject)
        """
        if not os.path.exists(self.ground_truth_file):
            return {}
        
        try:
            with open(self.ground_truth_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading ground truth: {e}")
            return {}
    
    def save_ground_truth(self) -> bool:
        """
        Save ground truth labels to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.ground_truth_file), exist_ok=True)
            with open(self.ground_truth_file, 'w') as f:
                json.dump(self.ground_truth, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving ground truth: {e}")
            return False
    
    def add_label(self, resume_name: str, should_shortlist: bool) -> None:
        """
        Add a ground truth label for a resume
        
        Args:
            resume_name: Name of the resume file
            should_shortlist: True if resume should be shortlisted, False otherwise
        """
        self.ground_truth[resume_name] = should_shortlist
        self.save_ground_truth()
    
    def add_batch_labels(self, labels: Dict[str, bool]) -> None:
        """
        Add multiple ground truth labels at once
        
        Args:
            labels: Dictionary mapping resume names to labels
        """
        self.ground_truth.update(labels)
        self.save_ground_truth()
    
    def evaluate(self, results: List[Dict], threshold: float = SHORTLIST_THRESHOLD) -> EvaluationMetrics:
        """
        Evaluate model predictions against ground truth
        
        Args:
            results: List of result dictionaries from the screening process
            threshold: Score threshold for shortlisting
            
        Returns:
            EvaluationMetrics object with all metrics
        """
        tp = tn = fp = fn = 0
        
        for result in results:
            resume_name = result.get('resume_name', '')
            
            # Skip if no ground truth label exists
            if resume_name not in self.ground_truth:
                continue
            
            # Get prediction and ground truth
            predicted_score = result.get('scores', {}).get('final_score', 0)
            predicted_shortlist = predicted_score >= threshold
            actual_shortlist = self.ground_truth[resume_name]
            
            # Update confusion matrix
            if predicted_shortlist and actual_shortlist:
                tp += 1
            elif not predicted_shortlist and not actual_shortlist:
                tn += 1
            elif predicted_shortlist and not actual_shortlist:
                fp += 1
            elif not predicted_shortlist and actual_shortlist:
                fn += 1
        
        total = tp + tn + fp + fn
        
        if total == 0:
            return EvaluationMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Calculate metrics
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            total_samples=total
        )
    
    def get_misclassified(self, results: List[Dict], threshold: float = SHORTLIST_THRESHOLD) -> Tuple[List[Dict], List[Dict]]:
        """
        Get false positives and false negatives
        
        Args:
            results: List of result dictionaries from the screening process
            threshold: Score threshold for shortlisting
            
        Returns:
            Tuple of (false_positives, false_negatives) as lists of result dicts
        """
        false_positives = []
        false_negatives = []
        
        for result in results:
            resume_name = result.get('resume_name', '')
            
            if resume_name not in self.ground_truth:
                continue
            
            predicted_score = result.get('scores', {}).get('final_score', 0)
            predicted_shortlist = predicted_score >= threshold
            actual_shortlist = self.ground_truth[resume_name]
            
            if predicted_shortlist and not actual_shortlist:
                false_positives.append(result)
            elif not predicted_shortlist and actual_shortlist:
                false_negatives.append(result)
        
        return false_positives, false_negatives
    
    def threshold_analysis(self, results: List[Dict], thresholds: List[float] = None) -> pd.DataFrame:
        """
        Analyze model performance across different thresholds
        
        Args:
            results: List of result dictionaries
            thresholds: List of threshold values to test (default: 0.5 to 0.9)
            
        Returns:
            DataFrame with metrics for each threshold
        """
        if thresholds is None:
            thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
        
        analysis = []
        for threshold in thresholds:
            metrics = self.evaluate(results, threshold)
            row = {'threshold': threshold}
            row.update(metrics.to_dict())
            analysis.append(row)
        
        return pd.DataFrame(analysis)
    
    def get_score_distribution(self, results: List[Dict]) -> Dict[str, List[float]]:
        """
        Get distribution of final scores for visualization.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Dictionary with 'all', 'tp', 'tn', 'fp', 'fn' score lists
        """
        dist = {
            'all': [],
            'tp': [], 'tn': [], 'fp': [], 'fn': []
        }
        
        threshold = SHORTLIST_THRESHOLD
        
        for result in results:
            score = result.get('scores', {}).get('final_score', 0)
            dist['all'].append(score)
            
            resume_name = result.get('resume_name', '')
            if resume_name in self.ground_truth:
                actual = self.ground_truth[resume_name]
                predicted = score >= threshold
                
                if predicted and actual: dist['tp'].append(score)
                elif not predicted and not actual: dist['tn'].append(score)
                elif predicted and not actual: dist['fp'].append(score)
                elif not predicted and actual: dist['fn'].append(score)
                
        return dist

    def get_coverage(self, results: List[Dict]) -> Dict[str, float]:
        """
        Calculate what percentage of resumes have ground truth labels
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Dictionary with coverage statistics
        """
        total_resumes = len(results)
        labeled_resumes = sum(1 for r in results if r.get('resume_name', '') in self.ground_truth)
        
        return {
            'total_resumes': total_resumes,
            'labeled_resumes': labeled_resumes,
            'coverage_percentage': (labeled_resumes / total_resumes * 100) if total_resumes > 0 else 0,
            'unlabeled_resumes': total_resumes - labeled_resumes
        }


def create_sample_ground_truth():
    """
    Create a sample ground truth file template
    
    Example format:
    {
        "john_doe_resume.pdf": true,
        "jane_smith_resume.pdf": false,
        ...
    }
    """
    sample = {
        "example_resume_1.pdf": True,
        "example_resume_2.pdf": False,
        "example_resume_3.pdf": True
    }
    
    file_path = "data/ground_truth_template.json"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(sample, f, indent=2)
    
    print(f"Sample ground truth template created at: {file_path}")
    print("\nFormat:")
    print("  - Key: Resume filename")
    print("  - Value: true (should shortlist) or false (should reject)")


if __name__ == "__main__":
    # Create sample template when run directly
    create_sample_ground_truth()

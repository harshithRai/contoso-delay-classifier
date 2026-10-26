"""Regression for real AutoML DataFrame outputs and delayed-class column order."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ml'))
from common import FEATURES,evaluate


class ProbabilityOutputs(unittest.TestCase):
    def test_dataframe_and_numpy_preserve_delayed_class_metrics(self):
        frame=pd.DataFrame({name:[0]*4 for name in FEATURES})
        frame['delayed']=[0,0,1,1]
        class ArrayModel:
            classes_=np.array([0,1])
            def predict(self,x):return np.array([0,1,0,1])
            def predict_proba(self,x):return np.array([[.9,.1],[.4,.6],[.6,.4],[.1,.9]])
        class AutoMLModel:
            classes_=np.array([1,0])
            def predict(self,x):return pd.DataFrame({'prediction':[0,1,0,1]})
            def predict_proba(self,x):return pd.DataFrame({1:[.1,.6,.4,.9],0:[.9,.4,.6,.1]})
        expected={'auc':.75,'accuracy':.5,'precision':.5,'recall':.5,'f1':.5,'confusionMatrix':[[1,1],[1,1]]}
        for model in [ArrayModel(),AutoMLModel()]:self.assertEqual(evaluate(model,frame),expected)

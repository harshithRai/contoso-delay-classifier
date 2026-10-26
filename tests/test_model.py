"""Check real trained-model artifacts and class-wise metric arithmetic."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class ModelReportTest(unittest.TestCase):
    def test_report_is_honest_and_metrics_agree(self):
        report=json.loads((ROOT/'evidence/local-training.json').read_text())
        self.assertEqual(report['source'],'local-baseline')
        for run in [report['best'],report['runnerUp']]:
            self.assertFalse(run['deployed']);self.assertEqual(run['testRows'],2000)
            m=run['metrics'];tn,fp=m['confusionMatrix'][0];fn,tp=m['confusionMatrix'][1]
            self.assertEqual(tn+fp+fn+tp,2000)
            self.assertAlmostEqual(m['precision'],tp/(tp+fp));self.assertAlmostEqual(m['recall'],tp/(tp+fn))
            self.assertGreaterEqual(m['auc'],0);self.assertLessEqual(m['auc'],1)
if __name__=='__main__':unittest.main()

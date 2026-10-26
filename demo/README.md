# Contoso Azure demo

[Watch or download the silent MP4](https://github.com/harshithRai/contoso-delay-classifier/releases/download/demo-2026-10-27/contoso-delay-demo-silent.mp4) (3 minutes 47 seconds; about 3.9 MB).

![Live prediction](poster.jpg)

The video covers architecture, actual AutoML metrics and limitations, a fresh live prediction, the same request in Cosmos Data Explorer, the health panel and load report, a deliberate wrong-key failure and restored inference.

The silent version contains no audio track. The assignment requires a screen recording showing the flow and does not specify narration.

The footage consists of actual Brave window frames captured approximately once per second during the demo. The original chapter timing was prepared for the optional narrated version. It is not a reconstruction of Azure screens. Screen sampling means the pointer motion is less smooth than a conventional high-frame-rate recording. [Optional narrated MP4](https://github.com/harshithRai/contoso-delay-classifier/releases/download/demo-2026-10-27/contoso-delay-demo.mp4), [transcript](narration.md) and [chapter timings](chapters.json) are available.

The saved video's request IDs are independently verified in [azure-video.json](../evidence/azure-video.json). The exact failure and recovery cohorts are preserved, including successes during settings propagation. Model recall and load-test errors are disclosed in the main README.

The real API model key is restored. Training clusters are deleted. The live endpoint remains active for demo/grading and must be deleted afterward.

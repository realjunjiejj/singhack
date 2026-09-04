# Separate analytics, presentation, and language generation

Python and pandas will ingest the challenge files, calculate deterministic metrics, apply Safety Overrides, and emit validated Evidence Packets. A polished Next.js workbench will render those packets and remain usable without an external model. A constrained AI endpoint may draft structured explanations and Conversation Plans from one Evidence Packet at a time, with cached validated output available when the live service is unavailable.

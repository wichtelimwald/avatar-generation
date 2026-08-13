"""
Shared Avatar Generation — Configuration

Default values for Leonardo.ai API and generation parameters.
Project-specific overrides are loaded from JSON character definition files.
"""

# ---------------------------------------------------------------------------
# Leonardo.ai API
# ---------------------------------------------------------------------------
LEONARDO_API_BASE = "https://cloud.leonardo.ai/api/rest/v1"

# Default generation parameters (can be overridden per-project via JSON)
DEFAULT_GENERATION_PARAMS = {
    "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
    "width": 1024,
    "height": 1024,
    "num_images": 1,
    "guidance_scale": 7,
    "num_inference_steps": 30,
    "alchemy": True,
}

# Default prompt max length (Leonardo.ai API limit)
DEFAULT_PROMPT_MAX_LENGTH = 1500

# Rate limiting
RATE_LIMIT_DELAY_SECONDS = 10

"""
Captcha Solver Module
Handles captcha solving using Azure OpenAI GPT-4 Vision API with JSON output
"""
import base64
import json
from openai import AzureOpenAI
from PIL import Image
import io


class CaptchaSolver:
    """Solves captcha images using Azure OpenAI GPT-4 Vision API"""

    def __init__(self, config_path='config.json'):
        # Load configuration from file
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Azure OpenAI configuration from config file
        azure_config = config.get('azure_openai', {})
        self.endpoint = azure_config.get('endpoint')
        self.deployment = azure_config.get('deployment')
        self.api_version = azure_config.get('api_version')
        self.subscription_key = azure_config.get('subscription_key')

        # Initialize Azure OpenAI client
        print("Initializing Azure OpenAI GPT-4 Vision...")
        self.client = AzureOpenAI(
            api_key=self.subscription_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        print("Azure OpenAI initialized successfully!")

    def solve_captcha(self, image_bytes):
        """
        Solve captcha from image bytes using GPT-4 Vision

        Args:
            image_bytes: Raw image bytes of the captcha

        Returns:
            Extracted captcha text (cleaned)
        """
        try:
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            # Call GPT-4 Vision API with JSON output mode
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a captcha reader. Read the alphanumeric text in captcha images. Return JSON with format: {\"captcha\": \"THE_TEXT_HERE\"}. Only include uppercase letters and numbers."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Read the text in this captcha image. Return only the captcha text in JSON format."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=100,
                temperature=0.1
            )

            # Parse JSON response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            # Extract captcha text
            captcha_text = result_json.get("captcha", "")

            # Clean and uppercase
            captcha_text = captcha_text.strip().upper()

            # Remove any non-alphanumeric characters
            captcha_text = ''.join(c for c in captcha_text if c.isalnum())

            return captcha_text

        except Exception as e:
            print(f"Error solving captcha with GPT-4 Vision: {e}")
            return ""

    def solve_from_page(self, page):
        """
        Extract and solve captcha directly from a playwright page

        Args:
            page: Playwright page object

        Returns:
            Solved captcha text
        """
        # Find the captcha image element
        captcha_img = page.locator('img[id^="captcha_"]').first

        # Get the image as bytes
        image_bytes = captcha_img.screenshot()

        # Solve the captcha
        return self.solve_captcha(image_bytes)

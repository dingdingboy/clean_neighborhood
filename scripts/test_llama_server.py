#!/usr/bin/env python3
"""
Test script to verify llama-server is working with the GGUF model.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from ai.vlm_engine import LlamaCppAnalyzer


async def test_health():
    """Test server health check."""
    print("Testing llama-server health...")

    async with LlamaCppAnalyzer() as analyzer:
        healthy = await analyzer.health_check()

        if healthy:
            print("✓ Server is healthy and responding")
            return True
        else:
            print("✗ Server is not responding")
            print("\nMake sure llama-server is running:")
            print("  ./scripts/start_llama_server.sh")
            return False


async def test_analysis(image_path: str = None):
    """Test image analysis."""
    print(f"\nTesting image analysis...")

    # Create a test image if none provided
    if not image_path:
        from PIL import Image, ImageDraw, ImageFont
        import tempfile

        # Create a simple test image with text
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)

        # Draw some shapes
        draw.rectangle([20, 20, 100, 100], fill='blue', outline='black')
        draw.ellipse([120, 50, 200, 130], fill='red', outline='black')

        # Try to add text
        try:
            draw.text((20, 150), "Test Image\nStop Sign", fill='black')
        except:
            pass  # Font issues are ok

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img.save(f.name, 'JPEG')
            image_path = f.name
            print(f"Created test image: {image_path}")

    async with LlamaCppAnalyzer() as analyzer:
        try:
            result = await analyzer.analyze(
                image_paths=[image_path],
                text_context="Analyze this test image for any public interest issues."
            )

            print("\n✓ Analysis completed successfully")
            print(f"\nResults:")
            print(f"  Harmful content: {result.contains_harmful_content}")
            print(f"  Categories: {result.harmful_categories}")
            print(f"  Severity: {result.violation_severity}/10")
            print(f"  Action: {result.recommended_action}")
            print(f"  Geolocation confidence: {result.geolocation.confidence}")

            if result.raw_analysis:
                print(f"\n  Description: {result.raw_analysis.get('description', 'N/A')}")

            return True

        except Exception as e:
            print(f"\n✗ Analysis failed: {e}")
            return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("llama-server GGUF Model Test")
    print("=" * 60)

    # Test 1: Health check
    if not await test_health():
        print("\n❌ Health check failed. Cannot continue tests.")
        sys.exit(1)

    # Test 2: Analysis (optional, takes time)
    print("\n" + "-" * 60)
    test_analysis_input = input("\nRun analysis test? This takes ~30-60s [y/N]: ")

    if test_analysis_input.lower() == 'y':
        success = await test_analysis()
        if not success:
            print("\n❌ Analysis test failed")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

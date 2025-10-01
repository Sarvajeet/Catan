from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Navigate to the Catan game
    page.goto("http://localhost:5001")

    # Wait for the board to be rendered by looking for at least one hex tile
    # This ensures the JavaScript has fetched the state and built the UI
    expect(page.locator(".hex").first).to_be_visible(timeout=10000)

    # Take a screenshot of the entire page
    page.screenshot(path="jules-scratch/verification/catan-board-fix.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
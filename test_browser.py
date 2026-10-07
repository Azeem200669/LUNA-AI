from browser.browser_controller import BrowserController


browser = BrowserController()


print()
print("=" * 70)
print("       🌙 LUNA REAL GOOGLE CHROME TEST")
print("=" * 70)


try:

    print()
    print("TEST 1: Start Google Chrome")

    print(
        browser.open_chrome()
    )

    browser.wait(
        1
    )

    print()
    print("TEST 2: Open Google")

    print(
        browser.open_url(
            "https://www.google.com"
        )
    )

    browser.wait(
        2
    )

    print()
    print("TEST 3: Google Search")

    print(
        browser.google_search_interactive(
            "Python tutorials"
        )
    )

    browser.wait(
        3
    )

    print()
    print("TEST 4: YouTube Search")

    print(
        browser.youtube_search_interactive(
            "AI tutorials"
        )
    )

    browser.wait(
        3
    )

    print()
    print("TEST 5: Page Title")

    print(
        browser.get_title()
    )

    print()
    print("TEST 6: Current URL")

    print(
        browser.get_url()
    )

finally:

    browser.close()


print()
print("=" * 70)
print("                 ✅ TEST COMPLETE")
print("=" * 70)
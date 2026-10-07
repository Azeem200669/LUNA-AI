from browser.browser_controller import BrowserController


browser = BrowserController()


print()
print("=" * 75)
print("       🌙 LUNA WEBPAGE INTERACTION TEST")
print("=" * 75)


try:

    # ========================================================
    # TEST 1
    # ========================================================

    print()
    print("TEST 1: Start Chrome")

    print(
        browser.open_chrome()
    )

    browser.wait(
        1
    )

    # ========================================================
    # TEST 2
    # ========================================================

    print()
    print(
        "TEST 2: YouTube Search"
    )

    print(
        browser.youtube_search_interactive(
            "Python tutorials"
        )
    )

    browser.wait(
        2
    )

    # ========================================================
    # TEST 3
    # ========================================================

    print()
    print(
        "TEST 3: Page Title"
    )

    print(
        browser.get_title()
    )

    # ========================================================
    # TEST 4
    # ========================================================

    print()
    print(
        "TEST 4: Read Page"
    )

    page_text = (
        browser.get_page_text(
            max_length=1500
        )
    )

    print(
        page_text
    )

    # ========================================================
    # TEST 5
    # ========================================================

    print()
    print(
        "TEST 5: Visible Links"
    )

    links = (
        browser.get_visible_links(
            limit=10
        )
    )

    for index, link in enumerate(
        links,
        start=1
    ):

        print(
            f"{index}. "
            f"{link['text']}"
        )

    # ========================================================
    # TEST 6
    # ========================================================

    print()
    print(
        "TEST 6: Open First YouTube Result"
    )

    print(
        browser.click_first_youtube_result()
    )

    browser.wait(
        3
    )

    # ========================================================
    # TEST 7
    # ========================================================

    print()
    print(
        "TEST 7: Current URL"
    )

    print(
        browser.get_url()
    )

    # ========================================================
    # TEST 8
    # ========================================================

    print()
    print(
        "TEST 8: Current Title"
    )

    print(
        browser.get_title()
    )


except Exception as error:

    print()
    print(
        f"❌ ERROR: {error}"
    )


finally:

    browser.close()


print()
print("=" * 75)
print(
    "             ✅ INTERACTION TEST COMPLETE"
)
print("=" * 75)
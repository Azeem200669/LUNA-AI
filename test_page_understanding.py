from browser.browser_controller import BrowserController


browser = BrowserController()


print()
print("=" * 75)
print("       🌙 LUNA WEBPAGE UNDERSTANDING TEST")
print("=" * 75)


try:

    # ========================================================
    # TEST 1
    # ========================================================

    print()
    print("TEST 1: Start Google Chrome")

    result = (
        browser.open_chrome()
    )

    print(
        result
    )

    browser.wait(
        1
    )

    # ========================================================
    # TEST 2
    # ========================================================

    print()
    print("TEST 2: Search YouTube")

    result = (
        browser.youtube_search_interactive(
            "Python tutorials"
        )
    )

    print(
        result
    )

    browser.wait(
        2
    )

    # ========================================================
    # TEST 3
    # ========================================================

    print()
    print("TEST 3: Page title")

    print(
        browser.get_title()
    )

    # ========================================================
    # TEST 4
    # ========================================================

    print()
    print("TEST 4: Current URL")

    print(
        browser.get_url()
    )

    # ========================================================
    # TEST 5
    # ========================================================

    print()
    print("TEST 5: YouTube result titles")

    results = (
        browser.get_result_titles(
            limit=10
        )
    )

    if results:

        for index, title in enumerate(
            results,
            start=1
        ):

            print(
                f"{index}. {title}"
            )

    else:

        print(
            "No results found."
        )

    # ========================================================
    # TEST 6
    # ========================================================

    print()
    print("TEST 6: Read page")

    page_text = (
        browser.get_page_text(
            max_length=3000
        )
    )

    print(
        page_text
    )

    # ========================================================
    # TEST 7
    # ========================================================

    print()
    print("TEST 7: Visible links")

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
    # TEST 8
    # ========================================================

    print()
    print("TEST 8: Read page for AI")

    page = (
        browser.read_page_for_ai(
            max_length=3000
        )
    )

    if page["success"]:

        print(
            "\nTITLE:"
        )

        print(
            page["title"]
        )

        print(
            "\nURL:"
        )

        print(
            page["url"]
        )

        print(
            "\nTEXT:"
        )

        print(
            page["text"]
        )

    else:

        print(
            "ERROR:",
            page["error"]
        )

    # ========================================================
    # TEST 9
    # ========================================================

    print()
    print("TEST 9: Open first YouTube result")

    print(
        browser.click_first_youtube_result()
    )

    browser.wait(
        3
    )

    print()
    print(
        "New title:",
        browser.get_title()
    )

    print(
        "New URL:",
        browser.get_url()
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
print("             ✅ TEST COMPLETE")
print("=" * 75)
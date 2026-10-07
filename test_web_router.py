from web.web_router import WebRouter


router = WebRouter()


tests = [

    "Luna, search the web for the latest AI news",

    "what are the latest developments in artificial intelligence",

    "Luna search for Python tutorials",

    "Luna, today's AI news",

    "AI గురించి తాజా వార్తలు చెప్పు",

    "AI की ताज़ा खबरें बताओ",

]


print()
print("=" * 80)
print("             🌙 LUNA WEB ROUTER TEST")
print("=" * 80)


for number, command in enumerate(
    tests,
    start=1
):

    print()
    print("=" * 80)

    print(
        f"TEST {number}"
    )

    print(
        f"USER: {command}"
    )

    print("=" * 80)

    result = router.handle(
        command
    )

    print()

    if not result["handled"]:

        print(
            "❌ Not detected as a web request."
        )

        continue

    if not result["success"]:

        print(
            "❌ Web request failed."
        )

        print(
            result.get("error")
        )

        continue

    print(
        "✅ WEB REQUEST SUCCESSFUL"
    )

    print()
    print(
        "QUERY:"
    )

    print(
        result["query"]
    )

    print()
    print(
        "LANGUAGE:"
    )

    print(
        result["language"]
    )

    print()
    print(
        "SOURCES:"
    )

    for index, source in enumerate(
        result["results"],
        start=1
    ):

        print(
            f"{index}. {source.get('title')}"
        )

        print(
            f"   {source.get('url')}"
        )

    print()
    print(
        "🤖 LUNA ANSWER:"
    )

    print()

    print(
        result["answer"]
    )


print()
print("=" * 80)
print("                 ✅ TEST COMPLETE")
print("=" * 80)
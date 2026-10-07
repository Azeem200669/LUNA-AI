from web.web_intelligence import WebIntelligence


web = WebIntelligence()


tests = [

    "latest AI news",

    "what are the latest developments in artificial intelligence",

    "latest Python news",

]


print()
print("=" * 80)
print("            🌙 LUNA TAVILY WEB INTELLIGENCE TEST")
print("=" * 80)


for number, query in enumerate(
    tests,
    start=1
):

    print()
    print("=" * 80)

    print(
        f"TEST {number}"
    )

    print(
        f"QUERY: {query}"
    )

    print("=" * 80)

    result = web.ask_web(
        query=query,
        language="en",
        max_results=5
    )

    if not result["success"]:

        print()
        print(
            "❌ SEARCH FAILED"
        )

        print(
            result["error"]
        )

        continue

    print()
    print(
        "✅ TAVILY SEARCH SUCCESSFUL"
    )

    print()
    print(
        "SOURCES:"
    )

    for index, source in enumerate(
        result["results"],
        start=1
    ):

        print()
        print(
            f"{index}. {source['title']}"
        )

        print(
            source["url"]
        )

        if source.get(
            "published_date"
        ):

            print(
                f"Date: {source['published_date']}"
            )

    print()
    print(
        "-" * 80
    )

    print(
        "🤖 LUNA ANSWER:"
    )

    print()

    print(
        result["answer"]
    )


print()
print("=" * 80)
print("                ✅ TAVILY TEST COMPLETE")
print("=" * 80)
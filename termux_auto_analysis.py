#!/usr/bin/env python3
"""Automatic stock search and analysis for Termux.
Searches web for recent A-share policy news and recommended stocks,
then runs FinGenius analysis and outputs short term buy suggestions.
"""
import asyncio
import re
from typing import List

from src.tool.web_search import WebSearch
from main import EnhancedFinGeniusAnalyzer

STOCK_CODE_PATTERN = re.compile(r"\b(60\d{4}|000\d{3}|001\d{3}|002\d{3}|603\d{3}|605\d{3})\b")
EXCLUDE_PREFIX = ("300", "301", "688", "689")

async def search_candidate_stocks(query: str = "A股 短线 股票 推荐") -> List[str]:
    """Search web pages for stock codes using WebSearch."""
    search = WebSearch()
    response = await search.execute(query=query, num_results=20, fetch_content=True)

    if not response or response.error:
        return []

    codes = set()
    for item in response.results:
        text = (item.title or "") + (item.description or "")
        if item.raw_content:
            text += item.raw_content
        for code in STOCK_CODE_PATTERN.findall(text):
            if not code.startswith(EXCLUDE_PREFIX):
                codes.add(code)
    return list(codes)

async def analyze_codes(codes: List[str], max_steps: int = 3, debate_rounds: int = 2):
    analyzer = EnhancedFinGeniusAnalyzer()
    results = {}
    for code in codes:
        res = await analyzer.analyze_stock(code, max_steps=max_steps, debate_rounds=debate_rounds)
        decision = res.get("battle_result", {}).get("final_decision")
        results[code] = decision
    return results

async def main(limit: int = 5):
    codes = await search_candidate_stocks()
    if not codes:
        print("未找到候选股票")
        return
    codes = codes[:limit]
    print(f"找到候选股票: {', '.join(codes)}")
    results = await analyze_codes(codes)
    print("\n分析结果：")
    for code, decision in results.items():
        decision_text = "看涨" if decision == "bullish" else "看跌" if decision == "bearish" else "未知"
        print(f"{code}: {decision_text}")
    buys = [c for c, d in results.items() if d == "bullish"]
    if buys:
        print("\n近期建议关注：" + ", ".join(buys))
    else:
        print("\n暂无明确买入建议")

if __name__ == "__main__":
    asyncio.run(main())

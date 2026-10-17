#!/usr/bin/env python3
from publishing.news_taxonomy import TAXONOMY, normalize_labels, stage_tag, news_mark_tag, impact_tag, category_tag, geo_tags

assert len(TAXONOMY["facets"]["stage"]) == 10
assert len(TAXONOMY["facets"]["category"]) == 5
assert len(TAXONOMY["facets"]["news_mark"]) == 5
assert len(TAXONOMY["facets"]["impact"]) == 4
assert stage_tag("法案提出") == "规划拟议"
assert stage_tag("试产中/9月底量产") == "推进中"
assert stage_tag("交易完成/并表") == "已生效/投产"
assert stage_tag("未知且不能归类") is None
assert news_mark_tag("今日新增/既有事件新增进展") == "事件进展"
assert news_mark_tag("今日新增/历史补漏/新事件") == "历史补录"
assert news_mark_tag("历史迁移") == "历史收录"
assert impact_tag("高（命中附件税号）；其他待HTS核验") == "高"
assert impact_tag("中（小家电/配件/直邮渠道）；低（大家电整机）") == "中"
assert category_tag("进口税") == "贸易与政策"
assert category_tag("竞品动态/制造布局/出口/市场与渠道") == "制造与产能"
assert category_tag("竞品动态/产品平台") == "市场与渠道"
assert geo_tags("欧洲/欧盟/德国/印尼/美国") == ["欧洲","欧盟","德国","印度尼西亚","美国"]
assert geo_tags("欧盟/中国") == ["欧盟","中国"]
assert "欧盟" not in geo_tags("德国/欧洲")
row = {"事件阶段":"法院裁决/措施继续有效","国家/地区":"美国/中国","新闻标注":"今日新增/既有事件新增进展","影响程度":"中高","事件分类":"贸易政策/贸易救济"}
out = normalize_labels(row)
assert out["raw"] == row
assert out["tags"]["category"] == "贸易与政策"
assert out["tags"]["geographies"] == ["美国","中国"]
assert out["tags"]["stage"] == "诉讼裁决"
assert out["tags"]["news_mark"] == "事件进展"
try:
    normalize_labels({**row, "内部负责人": "test"})
    raise AssertionError("unknown Sheet column was accepted")
except ValueError:
    pass
print("Standard five-facet public news taxonomy and ambiguity safeguards verified.")

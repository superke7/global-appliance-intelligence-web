#!/usr/bin/env python3
from publishing.news_taxonomy import TAXONOMY, normalize_labels, stage_tag, news_mark_tag, impact_tag, category_tag, geo_tags

assert len(TAXONOMY["facets"]["stage"]) == 10
assert len(TAXONOMY["facets"]["category"]) == 5
assert len(TAXONOMY["facets"]["news_mark"]) == 5
assert len(TAXONOMY["facets"]["impact"]) == 4
assert stage_tag("法案提出") == "规划拟议"
assert stage_tag("试产中/9月底量产") == "推进中"
assert stage_tag("已生效/谈判破裂") == "已生效/投产"
assert stage_tag("已公告/生效前最后谈判窗口") == "已宣布待实施"
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
assert geo_tags("以色列") == ["以色列"]
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

# Geographic coverage is expanded only for browsing, never by changing Sheet raw labels.
from publishing.news_taxonomy import expand_geo_filter_tags, GEO_HIERARCHY
assert len(GEO_HIERARCHY["organization_membership"]["欧盟"]) == 27
assert len(GEO_HIERARCHY["organization_membership"]["东盟"]) == 11
assert geo_tags("法国") == ["法国"]
assert set(expand_geo_filter_tags(geo_tags("法国"))) == {"法国", "欧盟", "欧洲"}
assert set(expand_geo_filter_tags(geo_tags("德国"))) == {"德国", "欧盟", "欧洲"}
assert "欧盟" not in expand_geo_filter_tags(geo_tags("英国"))
assert "欧洲" in expand_geo_filter_tags(geo_tags("英国"))
assert "欧盟" not in expand_geo_filter_tags(geo_tags("挪威"))
assert "欧盟" not in expand_geo_filter_tags(geo_tags("土耳其"))
assert "欧盟" not in expand_geo_filter_tags(geo_tags("欧洲"))
assert "法国" not in expand_geo_filter_tags(geo_tags("欧盟"))
assert set(expand_geo_filter_tags(geo_tags("越南"))) == {"越南", "东南亚", "东盟", "亚洲"}
assert set(expand_geo_filter_tags(geo_tags("东盟"))) == {"东盟", "东南亚", "亚洲"}
assert "东盟" in expand_geo_filter_tags(geo_tags("东帝汶"))
assert set(expand_geo_filter_tags(geo_tags("墨西哥"))) == {"墨西哥", "北美", "拉美"}
assert "南美" not in expand_geo_filter_tags(geo_tags("墨西哥"))
assert set(expand_geo_filter_tags(geo_tags("巴西"))) == {"巴西", "南美", "拉美"}
assert "大洋洲" in expand_geo_filter_tags(geo_tags("澳大利亚"))
assert set(expand_geo_filter_tags(geo_tags("法国/越南"))) == {"法国","越南","欧盟","欧洲","东盟","东南亚","亚洲"}
# A bare region is not treated as every country/member in that region.
assert "欧盟" not in expand_geo_filter_tags(geo_tags("欧洲"))
assert "法国" not in expand_geo_filter_tags(geo_tags("欧洲"))

print("Standard five-facet public news taxonomy and ambiguity safeguards verified.")

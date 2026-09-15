"""Server-side PDF reports for governed institutional-intelligence results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import json
import os
import re
from typing import Any, Dict, Iterable, List, Sequence
from urllib.parse import urlparse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    KeepTogether,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings


PDF_TEMPLATE_VERSION = "1.0"
MAX_SECTION_ITEMS = 100


@dataclass(frozen=True)
class PdfReport:
    content: bytes
    filename: str
    report_id: str


class IntelligencePdfService:
    """Render live or partially completed intelligence results as a formal PDF."""

    WORKFLOW_META = {
        "realtime-research": {
            "title": "实时信息检索报告",
            "subtitle": "X 与公共开放信息 - 尽力覆盖",
            "prefix": "realtime-intelligence",
        },
        "project-risk": {
            "title": "项目风险情报报告",
            "subtitle": "项目级风险、地面信号与人工复核动作",
            "prefix": "project-risk-intelligence",
        },
        "geopolitical-impact": {
            "title": "地缘融资推演报告",
            "subtitle": "融资影响传导、情景推演与策略选择",
            "prefix": "geopolitical-financing",
        },
        "sanctions-news": {
            "title": "制裁与负面新闻审查报告",
            "subtitle": "合规审查公共信息线索",
            "prefix": "sanctions-news",
        },
        "market-funding": {
            "title": "市场与资金环境分析报告",
            "subtitle": "利率、汇率、信用利差、商品价格与融资条件",
            "prefix": "market-funding",
        },
        "research-agent": {
            "title": "研究与数据 Agent 分析报告",
            "subtitle": "可核验数据分析与计算结果",
            "prefix": "research-agent",
        },
    }

    SCOPE_LABELS = {
        "query": "主题 / 问题",
        "keywords": "关键词与别名",
        "date_from": "开始日期",
        "date_to": "结束日期",
        "source_channels": "信息通道",
        "max_results": "最大结果数",
        "country": "国家/地区 / 地区",
        "project_name": "项目名称",
        "product_type": "金融产品",
        "risk_focus": "风险维度",
        "window_days": "实时证据窗口（天）",
        "monitoring_question": "决策问题",
        "issue": "地缘事件 / 政策变化",
        "regions": "重点地区 / 国家/地区",
        "actors": "重点行为方",
        "product_types": "金融产品",
        "horizon": "决策周期",
        "decision_question": "管理层决策问题",
        "workspace_id": "工作区",
    }

    TOKEN_LABELS = {
        "x": "X 公开内容",
        "public": "公共网页",
        "rising": "上升",
        "stable": "稳定",
        "falling": "下降",
        "unknown": "未知",
        "low": "低",
        "moderate": "中等",
        "high": "高",
        "critical": "严重",
        "unrated": "未评级",
        "continue": "继续并保持监测",
        "adjust_terms": "调整融资条款",
        "pause_for_review": "暂停并专项复核",
        "accelerate": "满足条件后加速",
        "escalate": "升级至管理层",
        "now": "立即",
        "7_days": "7 天内",
        "30_days": "30 天内",
        "monitor": "持续监测",
        "quarter": "本季度",
        "baseline": "基准情景",
        "stress": "压力情景",
        "opportunity": "机会情景",
        "medium": "中等",
        "source_available": "来源可访问",
        "verified_source": "来源已核验",
        "reported_claim": "媒体转述",
        "opinion": "公开观点",
        "unverified": "未验证",
        "sourced": "有来源",
        "inference": "模型推断",
        "uncertain": "不确定",
    }

    DARK = colors.HexColor("#07110F")
    GREEN = colors.HexColor("#087C5B")
    PALE = colors.HexColor("#E9F5EF")
    LIME = colors.HexColor("#BCF26D")
    AMBER = colors.HexColor("#F5E9D3")
    PURPLE = colors.HexColor("#EEE8FA")
    LINE = colors.HexColor("#D8E0DB")
    TEXT = colors.HexColor("#263A34")
    MUTED = colors.HexColor("#68776F")
    SURFACE = colors.HexColor("#F7F9F7")

    def __init__(self) -> None:
        self.font_name = self._register_font()
        self.styles = self._build_styles()

    @staticmethod
    def _register_font() -> str:
        candidates = [
            settings.PDF_FONT_PATH,
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        for path in candidates:
            if not path or not os.path.isfile(path):
                continue
            try:
                pdfmetrics.registerFont(TTFont("GrokDemoCJK", path, subfontIndex=0))
                return "GrokDemoCJK"
            except Exception:
                continue
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        sample = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "ReportTitle",
                parent=sample["Title"],
                fontName=self.font_name,
                fontSize=23,
                leading=31,
                textColor=self.DARK,
                alignment=TA_LEFT,
                spaceAfter=4 * mm,
                wordWrap="CJK",
            ),
            "subtitle": ParagraphStyle(
                "ReportSubtitle",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=10,
                leading=16,
                textColor=self.GREEN,
                spaceAfter=7 * mm,
                wordWrap="CJK",
            ),
            "kicker": ParagraphStyle(
                "SectionKicker",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7,
                leading=10,
                textColor=self.GREEN,
                spaceBefore=4 * mm,
                spaceAfter=1.5 * mm,
                wordWrap="CJK",
            ),
            "heading": ParagraphStyle(
                "SectionHeading",
                parent=sample["Heading2"],
                fontName=self.font_name,
                fontSize=15,
                leading=21,
                textColor=self.DARK,
                spaceAfter=3.5 * mm,
                wordWrap="CJK",
            ),
            "body": ParagraphStyle(
                "ReportBody",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=9.2,
                leading=15.5,
                textColor=self.TEXT,
                spaceAfter=2.2 * mm,
                wordWrap="CJK",
            ),
            "small": ParagraphStyle(
                "ReportSmall",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7.4,
                leading=11.2,
                textColor=self.MUTED,
                wordWrap="CJK",
            ),
            "table_header": ParagraphStyle(
                "TableHeader",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7.2,
                leading=10,
                textColor=colors.white,
                alignment=TA_LEFT,
                wordWrap="CJK",
            ),
            "table_cell": ParagraphStyle(
                "TableCell",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7.6,
                leading=11.5,
                textColor=self.TEXT,
                wordWrap="CJK",
            ),
            "callout": ParagraphStyle(
                "Callout",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=10,
                leading=16.5,
                textColor=self.DARK,
                wordWrap="CJK",
            ),
            "right": ParagraphStyle(
                "RightMeta",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7.2,
                leading=10,
                textColor=self.MUTED,
                alignment=TA_RIGHT,
                wordWrap="CJK",
            ),
            "center": ParagraphStyle(
                "CenterMeta",
                parent=sample["BodyText"],
                fontName=self.font_name,
                fontSize=7.2,
                leading=10,
                textColor=self.MUTED,
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
        }

    @staticmethod
    def validate_result(workflow: str, result: Dict[str, Any]) -> None:
        if workflow not in IntelligencePdfService.WORKFLOW_META:
            raise ValueError("不支持的情报工作流")
        if result.get("workflow") != workflow:
            raise ValueError("分析结果与导出工作流不匹配")
        if result.get("status") not in {"live", "partial"}:
            raise ValueError("只有已完成或部分完成的真实分析结果可以导出")
        if not isinstance(result.get("analysis"), dict) or not result["analysis"]:
            raise ValueError("分析结果为空，无法生成 PDF")

    def generate(
        self,
        workflow: str,
        result: Dict[str, Any],
        query_context: Dict[str, Any],
    ) -> PdfReport:
        self.validate_result(workflow, result)
        meta = self.WORKFLOW_META[workflow]
        audit = result.get("audit") or {}
        report_id = self._clean(audit.get("request_id") or "untracked", 100)
        exported_at = datetime.now(timezone.utc)
        subject = self._report_subject(workflow, query_context)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=17 * mm,
            leftMargin=17 * mm,
            topMargin=22 * mm,
            bottomMargin=19 * mm,
            title=f"{meta['title']} - {subject}",
            author="Grok Demo",
            subject=meta["subtitle"],
            creator=f"Grok Demo PDF Template {PDF_TEMPLATE_VERSION}",
        )
        story: List[Any] = []
        story.extend(self._cover(workflow, result, query_context, exported_at))
        if workflow == "realtime-research":
            story.extend(self._realtime_sections(result))
        elif workflow == "project-risk":
            story.extend(self._project_risk_sections(result))
        else:
            story.extend(self._generic_sections(result))
        story.extend(self._evidence_and_audit(result, exported_at))

        doc.build(
            story,
            onFirstPage=lambda canvas, current_doc: self._page_decor(
                canvas, current_doc, meta["title"], report_id
            ),
            onLaterPages=lambda canvas, current_doc: self._page_decor(
                canvas, current_doc, meta["title"], report_id
            ),
        )
        content = buffer.getvalue()
        if not content.startswith(b"%PDF-") or len(content) < 1000:
            raise RuntimeError("PDF 生成结果无效")
        stamp = exported_at.strftime("%Y%m%d-%H%M%S")
        filename = f"{meta['prefix']}-{self._filename_part(subject)}-{stamp}.pdf"
        return PdfReport(content=content, filename=filename, report_id=report_id)

    def _cover(
        self,
        workflow: str,
        result: Dict[str, Any],
        query_context: Dict[str, Any],
        exported_at: datetime,
    ) -> List[Any]:
        meta = self.WORKFLOW_META[workflow]
        audit = result.get("audit") or {}
        status_label = "已完成" if result.get("status") == "live" else "部分完成"
        evidence_label = "有引用" if result.get("evidence") else "未验证"
        story: List[Any] = [
            Spacer(1, 3 * mm),
            self._paragraph("GROK DECISION INTELLIGENCE", "kicker"),
            self._paragraph(meta["title"], "title"),
            self._paragraph(meta["subtitle"], "subtitle"),
        ]
        status_table = Table(
            [[
                self._paragraph(f"结果状态\n{status_label}", "small"),
                self._paragraph(f"证据质量\n{evidence_label}", "small"),
                self._paragraph(
                    f"分析生成时间\n{self._format_time(audit.get('generated_at'))}",
                    "small",
                ),
                self._paragraph(
                    f"PDF 导出时间\n{exported_at.strftime('%Y-%m-%d %H:%M UTC')}",
                    "small",
                ),
            ]],
            colWidths=[44 * mm, 40 * mm, 49 * mm, 44 * mm],
        )
        status_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.PALE),
            ("BOX", (0, 0), (-1, -1), 0.6, self.LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, self.LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([status_table, Spacer(1, 7 * mm)])
        story.extend(self._section_title("报告范围", "分析范围"))
        scope_rows = []
        for key, label in self.SCOPE_LABELS.items():
            if key not in query_context or query_context.get(key) in (None, "", []):
                continue
            scope_rows.append([label, self._display_value(query_context.get(key))])
        if not scope_rows:
            scope_rows = [["范围", "未随导出请求提供；请结合报告审计信息复核。"]]
        story.append(self._key_value_table(scope_rows))
        return story

    def _realtime_sections(self, result: Dict[str, Any]) -> List[Any]:
        analysis = result.get("analysis") or {}
        counts = result.get("counts") or {}
        story: List[Any] = []
        story.extend(self._summary_block(
            "研究结论",
            "实时信息综述",
            analysis.get("executive_summary"),
            analysis.get("coverage_note") or "结果为尽力覆盖，不代表 X 或公共网络的全量导出。",
            self.AMBER,
        ))
        story.extend(self._section_title("覆盖说明", "检索覆盖"))
        story.append(self._key_value_table([
            ["X 内容", counts.get("x", 0)],
            ["公共网页", counts.get("public", 0)],
            ["可访问引用", counts.get("citations", len(result.get("evidence") or []))],
            ["覆盖标记", result.get("coverage") or "best_effort"],
        ], label_width=34 * mm))

        trends = analysis.get("trends") or []
        story.extend(self._section_title("趋势信号", "主题与趋势"))
        story.append(self._data_table(
            ["趋势", "方向", "证据依据", "来源映射"],
            [[
                item.get("label"), self._token(item.get("direction")), item.get("evidence"),
                item.get("source_refs") or "未映射",
            ] for item in trends[:MAX_SECTION_ITEMS]],
            [31 * mm, 19 * mm, 80 * mm, 47 * mm],
            empty="本次没有形成可验证的趋势。",
        ))

        items = result.get("items") or analysis.get("items") or []
        story.extend(self._section_title("检索结果", "原始信息流"))
        item_rows = []
        for item in items[:MAX_SECTION_ITEMS]:
            body = item.get("original_text") or item.get("content_excerpt") or "未返回可验证正文"
            if item.get("source_type") == "x" and item.get("original_text") and item.get("content_excerpt"):
                body = f"X 原文：\n{item.get('original_text')}\n\n中文说明：\n{item.get('content_excerpt')}"
            item_rows.append([
                self._token(item.get("source_type") or "public"),
                item.get("author") or "未知发布者",
                item.get("published_at") or "时间未知",
                f"{item.get('title') or '未命名来源'}\n{body}",
                self._token(item.get("evidence_status") or "unverified"),
            ])
        story.append(self._data_table(
            ["通道", "作者 / 发布方", "时间", "原文 / 摘要", "证据状态"],
            item_rows,
            [14 * mm, 29 * mm, 28 * mm, 81 * mm, 25 * mm],
            empty="本次没有返回可导出的原始信息条目。",
        ))
        story.extend(self._simple_list("重要未知项", "未知项", analysis.get("unknowns") or []))
        return story

    def _project_risk_sections(self, result: Dict[str, Any]) -> List[Any]:
        analysis = result.get("analysis") or {}
        story: List[Any] = []
        story.extend(self._summary_block(
            "风险结论",
            "管理层风险简报",
            analysis.get("executive_summary"),
            analysis.get("direct_assessment") or "本次没有形成直接判断，需人工检查来源。",
            self.AMBER,
        ))
        story.extend(self._section_title("风险雷达", "五维风险与趋势"))
        story.append(self._data_table(
            ["维度", "评分", "等级", "趋势", "依据"],
            [[
                item.get("label") or item.get("dimension"), item.get("score", "未评级"),
                self._token(item.get("level") or "unrated"), self._token(item.get("trend") or "unknown"),
                item.get("rationale") or "未提供",
            ] for item in (analysis.get("risk_dimensions") or [])[:MAX_SECTION_ITEMS]],
            [30 * mm, 15 * mm, 21 * mm, 20 * mm, 91 * mm],
            empty="本次没有足够证据形成风险评分。",
        ))
        story.extend(self._section_title("实时信号", "事件与舆情时间线"))
        story.append(self._data_table(
            ["时间", "事件", "证据状态", "项目影响", "来源映射"],
            [[
                item.get("observed_at") or "时间未知", item.get("title"),
                self._token(item.get("evidence_status") or "unverified"), item.get("impact"),
                item.get("source_refs") or "未映射",
            ] for item in (analysis.get("events") or [])[:MAX_SECTION_ITEMS]],
            [23 * mm, 37 * mm, 25 * mm, 58 * mm, 34 * mm],
            empty="本次没有可展示的实时事件。",
        ))
        story.extend(self._section_title("决策选项", "建议复核动作"))
        story.append(self._data_table(
            ["动作", "紧迫度", "负责人", "可观察触发条件", "判断依据"],
            [[
                self._token(item.get("action")), self._token(item.get("urgency")), item.get("owner"),
                item.get("trigger"), item.get("rationale"),
            ] for item in (analysis.get("decision_options") or [])[:MAX_SECTION_ITEMS]],
            [24 * mm, 20 * mm, 25 * mm, 50 * mm, 58 * mm],
            empty="本次没有形成复核动作。",
        ))
        story.extend(self._simple_list("持续观察", "后续观察项", analysis.get("watch_items") or []))
        story.extend(self._simple_list("分析假设", "关键假设", analysis.get("assumptions") or []))
        return story

    def _generic_sections(self, result: Dict[str, Any]) -> List[Any]:
        """Generic PDF sections for any intelligence workflow."""
        analysis = result.get("analysis") or {}
        story: List[Any] = []
        story.extend(self._summary_block(
            "分析结论",
            "综述",
            analysis.get("executive_summary") or result.get("output_text"),
            analysis.get("direct_assessment") or analysis.get("market_outlook") or analysis.get("methodology") or "本次分析结论请参阅完整报告。",
            self.BLUE,
        ))
        # Findings / Key findings / Computation results
        findings = analysis.get("findings") or analysis.get("key_findings") or analysis.get("computation_results") or []
        if findings:
            story.extend(self._section_title("分析发现", "关键发现"))
            story.append(self._data_table(
                ["类别", "内容", "证据状态"],
                [[
                    f.get("category") or f.get("label") or f.get("indicator") or f.get("description", ""),
                    f.get("finding") or f.get("current_assessment") or f.get("result", ""),
                    self._token(f.get("evidence_status") or f.get("severity") or "pending"),
                ] for f in findings[:MAX_SECTION_ITEMS]],
                [40 * mm, 100 * mm, 28 * mm],
                empty="本次没有形成结构化发现。",
            ))
        # Risks / Warnings
        risks = analysis.get("risks_to_watch") or analysis.get("warnings") or analysis.get("unknowns") or []
        if risks:
            story.extend(self._simple_list("风险与未知项", "风险提示", risks))
        # Recommendations
        recs = analysis.get("recommendations") or analysis.get("decision_options") or []
        if recs:
            if isinstance(recs[0], dict):
                story.extend(self._section_title("建议", "后续建议"))
                story.append(self._data_table(
                    ["建议", "说明"],
                    [[r.get("action") or r.get("recommendation", ""), r.get("rationale") or r.get("trigger", "")] for r in recs[:MAX_SECTION_ITEMS]],
                    [50 * mm, 118 * mm],
                    empty="本次没有形成具体建议。",
                ))
            else:
                story.extend(self._simple_list("建议", "后续建议", recs))
        # Assumptions
        story.extend(self._simple_list("分析假设", "假设", analysis.get("assumptions") or []))
        return story

    def _geopolitical_sections(self, result: Dict[str, Any]) -> List[Any]:
        analysis = result.get("analysis") or {}
        story: List[Any] = []
        story.extend(self._summary_block(
            "战略结论",
            "战略直读",
            analysis.get("executive_summary"),
            analysis.get("direct_assessment") or "本次没有形成直接判断，需人工检查来源和假设。",
            self.PURPLE,
        ))
        story.extend(self._section_title("因果传导", "融资影响传导链"))
        story.append(self._data_table(
            ["驱动因素", "传导机制", "融资后果", "受影响方", "证据状态"],
            [[
                item.get("driver"), item.get("mechanism"), item.get("financing_effect"),
                item.get("affected_parties") or "待识别", self._token(item.get("evidence_status") or "uncertain"),
            ] for item in (analysis.get("transmission_paths") or [])[:MAX_SECTION_ITEMS]],
            [31 * mm, 54 * mm, 44 * mm, 27 * mm, 21 * mm],
            empty="本次没有形成可验证的传导链。",
        ))
        story.extend(self._section_title("情景分析", "融资情景推演"))
        story.append(self._data_table(
            ["情景 / 概率", "项目管道", "联合融资", "借贷意愿", "可行性", "风险转移", "早期信号"],
            [[
                f"{self._token(item.get('name') or '情景')} / {self._token(item.get('probability') or '未量化')}",
                item.get("pipeline_impact"), item.get("cofinancing_impact"),
                item.get("borrowing_appetite"), item.get("feasibility"),
                item.get("risk_transfer"), item.get("early_signals") or "未识别",
            ] for item in (analysis.get("scenarios") or [])[:3]],
            [25 * mm, 27 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm],
            empty="本次没有形成基准、压力或机会情景。",
        ))
        story.extend(self._section_title("决策选项", "策略选择与代价"))
        story.append(self._data_table(
            ["策略", "收益", "代价", "负责人 / 时机", "触发条件"],
            [[
                item.get("action"), item.get("upside"), item.get("downside"),
                f"{item.get('owner') or '待指定'} / {item.get('timing') or '待确定'}",
                item.get("trigger"),
            ] for item in (analysis.get("decision_options") or [])[:MAX_SECTION_ITEMS]],
            [32 * mm, 41 * mm, 41 * mm, 32 * mm, 31 * mm],
            empty="本次没有形成策略选项。",
        ))
        story.extend(self._simple_list("分析假设", "关键假设", analysis.get("assumptions") or []))
        story.extend(self._simple_list("重要未知项", "未知项", analysis.get("unknowns") or []))
        return story

    def _evidence_and_audit(
        self,
        result: Dict[str, Any],
        exported_at: datetime,
    ) -> List[Any]:
        evidence = result.get("evidence") or []
        audit = result.get("audit") or {}
        story: List[Any] = [PageBreak()]
        story.extend(self._section_title("证据来源", "来源账本"))
        source_rows = []
        for source in evidence[:MAX_SECTION_ITEMS]:
            url = self._clean(source.get("url") or "", 1400)
            source_rows.append([
                source.get("id") or "-",
                self._token(source.get("source_type") or "public"),
                source.get("title") or "未命名来源",
                self._token(source.get("verification_status") or "unverified"),
                self._link(url),
                source.get("excerpt") or "",
            ])
        story.append(self._data_table(
            ["编号", "通道", "来源", "核验状态", "链接", "摘录"],
            source_rows,
            [12 * mm, 16 * mm, 39 * mm, 25 * mm, 48 * mm, 37 * mm],
            empty="本次结果没有可访问引用，所有实时事实均需独立核验。",
            preformatted=True,
        ))

        story.extend(self._section_title("运行记录", "审计信息"))
        story.append(self._key_value_table([
            ["工作流", result.get("workflow")],
            ["提供方", audit.get("provider")],
            ["模型", audit.get("model")],
            ["区域", audit.get("region")],
            ["请求编号", audit.get("request_id")],
            ["工作区", audit.get("workspace_id")],
            ["分析生成时间", self._format_time(audit.get("generated_at"))],
            ["PDF 导出时间", exported_at.isoformat()],
            ["实际使用工具", audit.get("tools") or "无"],
            ["请求工具", audit.get("requested_tools") or "无"],
            ["降级工具", audit.get("degraded_tools") or "无"],
            ["覆盖契约", audit.get("coverage") or result.get("coverage") or "best_effort"],
            ["PDF 模板版本", PDF_TEMPLATE_VERSION],
        ], label_width=35 * mm))

        warnings = result.get("warnings") or []
        story.extend(self._simple_list("IMPORTANT NOTICE", "重要说明", warnings))
        story.append(self._callout(
            "本报告仅用于研究、风险复核与管理层决策支持，不构成收益承诺、交易指令或自动融资决定。"
            "X 公开观点、媒体转述和模型推断必须结合可访问来源独立核验。",
            self.AMBER,
        ))
        return story

    def _summary_block(
        self,
        kicker: str,
        title: str,
        summary: Any,
        direct: Any,
        callout_color: colors.Color,
    ) -> List[Any]:
        story = self._section_title(kicker, title)
        story.append(self._paragraph(summary or "本次没有返回可解析的摘要。", "body"))
        story.append(self._callout(direct, callout_color))
        return story

    def _simple_list(self, kicker: str, title: str, items: Iterable[Any]) -> List[Any]:
        values = list(items or [])[:MAX_SECTION_ITEMS]
        story = self._section_title(kicker, title)
        if not values:
            story.append(self._paragraph("本次没有记录相关内容。", "small"))
            return story
        rows = [[self._paragraph(f"{index:02d}", "center"), self._paragraph(item, "body")]
                for index, item in enumerate(values, 1)]
        table = Table(rows, colWidths=[13 * mm, 164 * mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), self.PALE),
            ("LINEBELOW", (0, 0), (-1, -2), 0.35, self.LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        return story

    def _section_title(self, kicker: str, title: str) -> List[Any]:
        return [KeepTogether([
            self._paragraph(kicker, "kicker"),
            self._paragraph(title, "heading"),
        ])]

    def _callout(self, value: Any, background: colors.Color) -> Table:
        table = Table([[self._paragraph(value or "未提供", "callout")]], colWidths=[177 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), background),
            ("BOX", (0, 0), (-1, -1), 0.6, self.LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return table

    def _key_value_table(
        self,
        rows: Sequence[Sequence[Any]],
        label_width: float = 38 * mm,
    ) -> Table:
        content = [[self._paragraph(row[0], "small"), self._paragraph(row[1], "table_cell")]
                   for row in rows]
        table = Table(content, colWidths=[label_width, 177 * mm - label_width])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), self.SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.5, self.LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, self.LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _data_table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        widths: Sequence[float],
        empty: str,
        preformatted: bool = False,
    ) -> Any:
        if not rows:
            return self._callout(empty, self.SURFACE)
        header_row = [self._paragraph(item, "table_header") for item in headers]
        data_rows = []
        for row in rows:
            cells = []
            for item in row:
                if preformatted and isinstance(item, Paragraph):
                    cells.append(item)
                else:
                    cells.append(self._paragraph(self._display_value(item), "table_cell"))
            data_rows.append(cells)
        table = LongTable([header_row, *data_rows], colWidths=list(widths), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DARK),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.5, self.LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, self.LINE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.SURFACE]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _paragraph(self, value: Any, style_name: str) -> Paragraph:
        if isinstance(value, Paragraph):
            return value
        text = self._clean(value)
        safe = escape(text).replace("\n", "<br/>")
        return Paragraph(safe or "-", self.styles[style_name])

    def _link(self, url: str) -> Paragraph:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return self._paragraph(url or "无可访问链接", "table_cell")
        safe_url = escape(url, quote=True)
        label = escape(self._clean(url, 220))
        return Paragraph(f'<link href="{safe_url}" color="#087C5B">{label}</link>', self.styles["table_cell"])

    @staticmethod
    def _display_value(value: Any) -> str:
        if value is None or value == "":
            return "-"
        if isinstance(value, (list, tuple, set)):
            return "、".join(IntelligencePdfService._clean(item, 600) for item in value) or "-"
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, bool):
            return "是" if value else "否"
        return IntelligencePdfService._clean(value)

    def _token(self, value: Any) -> str:
        cleaned = self._clean(value, 300)
        return self.TOKEN_LABELS.get(cleaned.lower(), cleaned)

    @staticmethod
    def _clean(value: Any, limit: int = 5000) -> str:
        if isinstance(value, (dict, list, tuple, set)):
            try:
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            except TypeError:
                value = str(value)
        text = str(value if value is not None else "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", text)
        text = text.strip()
        if len(text) > limit:
            return f"{text[:limit]}...（已截断）"
        return text

    @staticmethod
    def _format_time(value: Any) -> str:
        if not value:
            return "unknown"
        text = IntelligencePdfService._clean(value, 100)
        return text.replace("T", " ").replace("+00:00", " UTC")

    @staticmethod
    def _filename_part(value: Any) -> str:
        text = IntelligencePdfService._clean(value, 48)
        text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text).strip("-")
        return text or "report"

    @staticmethod
    def _report_subject(workflow: str, context: Dict[str, Any]) -> str:
        if workflow == "realtime-research":
            return IntelligencePdfService._clean(context.get("query") or "实时检索", 80)
        if workflow == "project-risk":
            return IntelligencePdfService._clean(context.get("project_name") or "项目风险", 80)
        return IntelligencePdfService._clean(context.get("issue") or "地缘融资", 80)

    def _page_decor(self, canvas: Any, doc: Any, title: str, report_id: str) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(self.DARK)
        canvas.rect(0, height - 10 * mm, width, 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(self.LIME)
        canvas.setFont(self.font_name, 7.2)
        canvas.drawString(17 * mm, height - 6.5 * mm, "GROK DEMO / 实时决策情报分析")
        canvas.setFillColor(self.MUTED)
        canvas.setFont(self.font_name, 6.8)
        canvas.drawString(17 * mm, 10 * mm, self._clean(title, 80))
        canvas.drawCentredString(width / 2, 10 * mm, f"REQUEST {self._clean(report_id, 42)}")
        canvas.drawRightString(width - 17 * mm, 10 * mm, f"PAGE {doc.page}")
        canvas.setStrokeColor(self.LINE)
        canvas.setLineWidth(0.4)
        canvas.line(17 * mm, 13 * mm, width - 17 * mm, 13 * mm)
        canvas.restoreState()


intelligence_pdf_service = IntelligencePdfService()

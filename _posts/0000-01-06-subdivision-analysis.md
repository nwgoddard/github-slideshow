---
layout: slide
title: "Subdivision Analysis — Key Findings"
slide-id: subdivision-analysis
---

<p style="color:#aaa; font-size:0.85rem; margin-bottom:1.2rem;">
  {{ site.data.realtyrates.developer_survey.quarter }} &nbsp;·&nbsp; RealtyRates.com Survey Data
</p>

{% assign sub = site.data.realtyrates.developer_survey.categories | where: "name", "Subdivisions & PUDs" | first %}
{% assign land_metric = sub.metrics | where: "name", "Land Acquisition Loan Rate" | first %}
{% assign ltv_metric  = sub.metrics | where: "name", "Max LTV - Land" | first %}
{% assign abs_metric  = sub.metrics | where: "name", "Absorption Rate" | first %}
{% assign eq_metric   = sub.metrics | where: "name", "Equity Requirement" | first %}
{% assign treasury    = site.data.realtyrates.indices.indices | where: "name", "10-Year Treasury" | first %}
{% assign prime       = site.data.realtyrates.indices.indices | where: "name", "Prime Rate" | first %}

<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1.5rem;">

  <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:6px; padding:1rem;">
    <div style="color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:.05em; margin-bottom:.3rem;">Land Loan Rate</div>
    <div style="font-size:1.6rem; font-weight:700; color:#4f8ef7;">
      {{ land_metric.low }}–{{ land_metric.high }}%
    </div>
    <div style="color:#666; font-size:0.8rem;">Avg {{ land_metric.avg }}% &nbsp;·&nbsp; {{ land_metric.unit }}</div>
  </div>

  <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:6px; padding:1rem;">
    <div style="color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:.05em; margin-bottom:.3rem;">Max LTV (Land)</div>
    <div style="font-size:1.6rem; font-weight:700; color:#4f8ef7;">
      {{ ltv_metric.low }}–{{ ltv_metric.high }}%
    </div>
    <div style="color:#666; font-size:0.8rem;">Avg {{ ltv_metric.avg }}%</div>
  </div>

  <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:6px; padding:1rem;">
    <div style="color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:.05em; margin-bottom:.3rem;">Absorption Rate</div>
    <div style="font-size:1.6rem; font-weight:700; color:#4caf7d;">
      {{ abs_metric.low }}–{{ abs_metric.high }} lots/mo
    </div>
    <div style="color:#666; font-size:0.8rem;">Avg {{ abs_metric.avg }} lots/month</div>
  </div>

  <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:6px; padding:1rem;">
    <div style="color:#888; font-size:0.75rem; text-transform:uppercase; letter-spacing:.05em; margin-bottom:.3rem;">Equity Requirement</div>
    <div style="font-size:1.6rem; font-weight:700; color:#f5c842;">
      {{ eq_metric.avg }}%
    </div>
    <div style="color:#666; font-size:0.8rem;">Range {{ eq_metric.low }}–{{ eq_metric.high }}%</div>
  </div>

</div>

<ul style="font-size:0.85rem; color:#bbb; line-height:1.8; padding-left:1.2rem;">
  <li>Land loans carry a <strong style="color:#f76f4f;">
    {% assign spread = land_metric.avg | minus: treasury.value %}{{ spread | round: 2 }}%
    spread</strong> over the 10-Yr Treasury ({{ treasury.value }}%)</li>
  <li>Lower LTV vs. stabilized commercial (65–75%) reflects <strong>development risk premium</strong></li>
  <li>Absorption rate is the primary feasibility lever — faster sales reduce carry cost</li>
  <li>Prime Rate ({{ prime.value }}%) sets the floor for construction credit lines</li>
</ul>

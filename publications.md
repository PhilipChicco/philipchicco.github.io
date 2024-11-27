---
layout: default
title: Publications
permalink: /publications/
---

<div class="section publications">
    <h2 class="gradient-text">Featured Publications</h2>
    <div class="publication-grid">
        {% for pub in site.data.publications.featured limit:3 %}
        <div class="publication-card featured">
            {% if pub.image %}
            <img src="{{ pub.image }}" alt="{{ pub.title }}" class="pub-image">
            {% endif %}
            <div class="pub-content">
                <h3>{{ pub.title }}</h3>
                <p class="authors">{{ pub.authors }}</p>
                <p class="venue"><strong>{{ pub.venue }}</strong>, {{ pub.year }}</p>
                {% if pub.pdf %}
                <a href="{{ pub.pdf }}" class="pub-link" target="_blank">PDF</a>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<div class="section all-publications">
    <h2 class="gradient-text">All Publications</h2>
    
    {% assign years = site.data.publications.all | map: "year" | uniq | sort | reverse %}
    
    {% for year in years %}
    <div class="year-section">
        <h3>{{ year }}</h3>
        {% assign year_pubs = site.data.publications.all | where: "year", year %}
        {% for pub in year_pubs %}
        <div class="publication-item">
            <div class="pub-content">
                <h4>{{ pub.title }}</h4>
                <p class="authors">{{ pub.authors }}</p>
                <p class="venue"><strong>{{ pub.venue }}</strong></p>
                <div class="pub-links">
                    {% if pub.pdf %}
                    <a href="{{ pub.pdf }}" class="pub-link" target="_blank">PDF</a>
                    {% endif %}
                    {% if pub.code %}
                    <a href="{{ pub.code }}" class="pub-link code" target="_blank">Code</a>
                    {% endif %}
                    {% if pub.doi %}
                    <a href="{{ pub.doi }}" class="pub-link doi" target="_blank">DOI</a>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endfor %}
</div>
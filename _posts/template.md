---
layout: default
title: "Title of Your News Item"
date: YYYY-MM-DD
categories: [news, publication, award, presentation]
description: "Brief description for meta tags and previews"
---

<div class="news-content reveal">
    <h1 class="gradient-text">{{ page.title }}</h1>
    <div class="news-meta">
        <span class="news-date">{{ page.date | date: "%B %d, %Y" }}</span>
        <span class="news-categories">
            {% for category in page.categories %}
            <span class="category-tag">{{ category }}</span>
            {% endfor %}
        </span>
    </div>

    <div class="news-body">
        <p>Your news content goes here. You can include:</p>
        
        <!-- For paper announcements -->
        <div class="paper-highlight">
            <h3>Paper Title</h3>
            <p class="authors">Author1, Author2, Author3</p>
            <p class="venue">Conference/Journal Name</p>
            <div class="paper-links">
                <a href="#" target="_blank">PDF</a>
                <a href="#" target="_blank">Code</a>
                <a href="#" target="_blank">Project Page</a>
            </div>
        </div>

        <!-- For other announcements -->
        <p>Regular paragraph text with <a href="#">linked content</a> and more details.</p>

        <!-- For images -->
        <div class="news-image">
            <img src="/path/to/image.jpg" alt="Description">
            <em>Image caption (optional)</em>
        </div>
    </div>
</div>
# Intro
A real-time social media trend analyzer that tracks public discussions and sentiment across major platforms. The system aggregates content and transforms it into structured data, enhanced with AI-generated insights.

# Key Features
- List of social media websites: hacker news, reddit, twitter, etc.
- AI generated structured data including comments trending.
- LLM friendly data output, great for developers to build their own applications based on the data.

# Tech
The content will be transformed into a unified format like:
```
{
    "title": "title",
    "url": "url",
    "content": "content", // optional
    "comments": [
        {"content": "comment content", "author": "comment author"}
    ],
    "published": "2025-01-10T09:51:07.769Z",
    "modified": "2025-01-10T09:51:07.769Z",
    // ai generated fields below
    "summary": "the summary of (the content of the url, title)",
    "summary_comment": "the key idea of the comments", // optional
    "keywords": ["keyword1", "keyword2", "keyword3"] // optional
}
```

```mermaid
graph TD
    subgraph GitHub-Action
        subgraph Sources
            A1[Reddit]
            A2[Hacker News]
            A3[Twitter]
            A1 & A2 & A3 --> A[Crawler]
        end

        A --> |Raw Data| B[Transformer]
        B --> |Structured Data| C[Data Processor]
    
        subgraph Processing
            C --> D[AI Enhancement]
            D --> |Add Summary| E[Content Summary]
            D --> |Add Keywords| F[Keyword Extraction]
            D --> |Add Insights| G[Comment Analysis]
        end
        
        subgraph Export
            E & F & G --> H[Exporter]
            H --> |Static File| I[JSON File]
            H --> |RSS Compatible| J[JSON Feed]
            H --> |Static Site| K[HTML]
        end
    end

    subgraph Consumers
        I --> |API| L[3rd Party Clients]
        J --> |Feed| M[RSS Readers]
        K --> |Website| X[GitHub Pages]
    end
```

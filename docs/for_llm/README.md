> all the docs in this folder are for the llm

# Tech
The content will be transformed into a unified format like:
```
{
    // original data
    "title": "title",
    "url": "url",
    "content": "content", // optional
    "comments": [
        {"content": "comment content", "author": "comment author"}
    ],
    "published": "2020-01-02T03:04:05Z", // optional
    /////////////////////////////
    "id": "id", // original id or generated id based on the url, for cache and deduplication with local db
    "created": "2025-01-10T09:51:07Z", // the fetched time
    "updated": "2025-01-10T09:51:07Z", // the last updated time, e.g. updated the comments
    // ai generated fields below
    "summary": "the summary(the content of the url, title)",
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

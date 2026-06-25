New-Item -ItemType Directory -Force .\public\img\authors | Out-Null

Copy-Item .\tolstoy-leo.png .\public\img\authors\tolstoy-leo.png -Force
Copy-Item .\austen-jane.png .\public\img\authors\austen-jane.png -Force
Copy-Item .\kafka-franz.png .\public\img\authors\kafka-franz.png -Force

npm run build
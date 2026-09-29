.PHONY: serve build new clean

serve: ## 本地预览(含草稿)
	hugo server -D

build: ## 构建静态站点到 public/
	hugo --gc --minify

new: ## 新建文章: make new slug=my-first-post
	hugo new content "posts/$(slug).md"

clean: ## 清理构建产物
	rm -rf public resources/_gen hugo_stats.json

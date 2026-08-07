MAIN = introduction_to_socialism
DIR = latex
TEX_DIR = latex_out
.PHONY: help pdf view epub tex clean test db compare

help:
	@echo "Usage:"
	@echo "  make pdf    - Build $(TEX_DIR)/$(MAIN).pdf"
	@echo "  make epub   - Build $(MAIN).epub"
	@echo "  make tex    - Build LaTeX files from RST sources"
	@echo "  make view   - Open $(TEX_DIR)/$(MAIN).pdf"
	@echo "  make clean  - Remove build artifacts"
	@echo "  make test   - Run Python tests"
	@echo "  make db      - Re-create articles.db from syllabus URLs"
	@echo "  make compare - Compare book RST against original articles"
	@echo "  make help   - Show this message"

pdf: $(TEX_DIR)/$(MAIN).pdf

epub: $(MAIN).epub

view: $(TEX_DIR)/$(MAIN).pdf
	xdg-open $(TEX_DIR)/$(MAIN).pdf

tex: $(wildcard rst/*.rst) $(wildcard rst/articles/*.rst) latex/$(MAIN).tex
	. $(HOME)/.local/bin/env && uv run rst2latex2 --fragment --main-template latex/$(MAIN).tex

test:
	. $(HOME)/.local/bin/env && uv run pytest -v

db:
	. $(HOME)/.local/bin/env && uv run python -m intro_to_socialism.build_db

compare:
	. $(HOME)/.local/bin/env && uv run python -m intro_to_socialism.compare_db

clean:
	$(RM) $(TEX_DIR)/$(MAIN).aux $(TEX_DIR)/$(MAIN).log $(TEX_DIR)/$(MAIN).toc $(TEX_DIR)/$(MAIN).out $(TEX_DIR)/$(MAIN).fls $(TEX_DIR)/$(MAIN).fdb_latexmk
	$(RM) -r epub $(MAIN).epub
	$(RM) -r xhtml_out

$(TEX_DIR)/$(MAIN).pdf: $(TEX_DIR)/$(MAIN).tex
	cd $(TEX_DIR) && latexmk -pdf -interaction=nonstopmode -halt-on-error $(MAIN)

$(TEX_DIR)/$(MAIN).tex: tex

$(MAIN).epub: $(wildcard rst/articles/*.rst) $(wildcard rst/chapter_*.rst)
	. $(HOME)/.local/bin/env && uv run python -m intro_to_socialism.build_epub
	. $(HOME)/.local/bin/env && uv run python -m intro_to_socialism.build_epub zip

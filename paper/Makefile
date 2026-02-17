.PHONY: pdf latex all clean

all: paper.pdf paper.tex

pdf: paper.pdf

latex: paper.tex

paper.pdf: paper.md references.bib
	pandoc paper.md \
		--from markdown \
		--to pdf \
		--pdf-engine=xelatex \
		--citeproc \
		--bibliography=references.bib \
		--number-sections \
		--toc \
		-V geometry:margin=1in \
		-V fontsize=11pt \
		-V colorlinks=true \
		-V mainfont="Times New Roman" \
		-V monofont="Menlo" \
		-V mathfont="STIX Two Math" \
		-o paper.pdf

paper.tex: paper.md references.bib
	pandoc paper.md \
		--from markdown \
		--to latex \
		--pdf-engine=xelatex \
		--citeproc \
		--bibliography=references.bib \
		--number-sections \
		--toc \
		-V geometry:margin=1in \
		-V fontsize=11pt \
		-V colorlinks=true \
		-V mainfont="Times New Roman" \
		-V monofont="Menlo" \
		-V mathfont="STIX Two Math" \
		--standalone \
		-o paper.tex

clean:
	rm -f paper.pdf paper.tex *.aux *.log *.out *.toc *.bbl *.blg

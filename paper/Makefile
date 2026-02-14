.PHONY: pdf clean

pdf: paper.pdf

paper.pdf: paper.md references.bib
	pandoc paper.md \
		--from markdown \
		--to pdf \
		--citeproc \
		--bibliography=references.bib \
		--number-sections \
		--toc \
		-V geometry:margin=1in \
		-V fontsize=11pt \
		-V colorlinks=true \
		-o paper.pdf

clean:
	rm -f paper.pdf *.aux *.log *.out *.toc *.bbl *.blg

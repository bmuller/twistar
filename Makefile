PYDOCTOR=pydoctor

docs:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package twistar --project-name=twistar --project-url=http://trac.butterfat.net/public/twistar --html-viewsource-base=http://trac.butterfat.net/public/twistar/browser --html-use-sorttable --html-use-splitlinks --html-shorten-lists
	lore --config template=doc/template.tpl doc/*.xhtml

test:
	trial twistar.tests
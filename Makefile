PYDOCTOR=pydoctor

doc:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package twistdb --project-name=twistdb --project-url=http://trac.butterfat.net/public/twistdb --html-viewsource-base=http://trac.butterfat.net/public/twistdb/browser --html-use-sorttable --html-use-splitlinks --html-shorten-lists

test:
	trial twistdb.tests
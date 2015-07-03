PYDOCTOR=pydoctor

docs:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package twistar --project-name=twistar --project-url=http://findingscience.com/twistar --html-use-sorttable --html-use-splitlinks --html-shorten-lists 
	lore --config template=doc/template.tpl doc/*.xhtml

test:
	trial twistar

install:
	python setup.py install

lint:
	pep8 --ignore=E303,E251,E201,E202 --max-line-length=140 ./twistar
	find ./twistar -name '*.py' | xargs pyflakes

# Inflector for Python

The Inflector is used for getting the plural and singular form of nouns. This piece of code helps on creating code that favors convention over configuration.

Only English and Spanish nouns are supported. The English version is a port of Ruby on Rails Inflector, while the Spanish Version has been developed from scratch with the help of Carles Sadurní.

Apart from converting singulars and plurals, this module also handles necessary string conversion for convention based applications like:

Available methods are:

## pluralize(word)

Pluralizes nouns.

## singularize(word)

Singularizes nouns.

## conditionalPlural(numer_of_records, word)

Returns the plural form of a word if first parameter is greater than 1

## titleize(word, uppercase = '')

Converts an underscored or CamelCase word into a sentence.
The titleize function converts text like "WelcomePage",
"welcome_page" or  "welcome page" to this "Welcome Page".
If the "uppercase" parameter is set to 'first' it will only
capitalize the first character of the title.

## camelize(word):

Returns given word as CamelCased
Converts a word like "send_email" to "SendEmail". It
will remove non alphanumeric character from the word, so
"who's online" will be converted to "WhoSOnline"

## underscore(word)

Converts a word "into_it_s_underscored_version"
Convert any "CamelCased" or "ordinary Word" into an
"underscored_word".
This can be really useful for creating friendly URLs.

## humanize(word, uppercase = '')

Returns a human-readable string from word
Returns a human-readable string from word, by replacing
underscores with a space, and by upper-casing the initial
character by default.
If you need to uppercase all the words you just have to
pass 'all' as a second parameter.


## variablize(word)

Same as camelize but first char is lowercased
Converts a word like "send_email" to "sendEmail". It
will remove non alphanumeric character from the word, so
"who's online" will be converted to "whoSOnline"
return self.Inflector.variablize(word)

## tableize(class_name)

Converts a class name to its table name according to rails
naming conventions. Example. Converts "Person" to "people" 

## classify(table_name)

Converts a table name to its class name according to rails
naming conventions. Example: Converts "people" to "Person" 

## ordinalize(number)
Converts number to its ordinal form.
This method converts 13 to 13th, 2 to 2nd ...

## unaccent(text)

Transforms a string to its unaccented version. 
This might be useful for generating "friendly" URLs

## urlize(text)

Transform a string its unaccented and underscored
version ready to be inserted in friendly URLs

## foreignKey(class_name, separate_class_name_and_id_with_underscore = 1)

Returns class_name in underscored form, with "_id" tacked on at the end. 
This is for use in dealing with the database.

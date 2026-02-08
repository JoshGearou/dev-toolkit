/**
 * Creates a custom menu in the Google Docs UI when the document is opened.
 */
function onOpen() {
  DocumentApp.getUi()
    .createMenu('Link Tools')
    .addItem('go/linkify', 'goLinkify')
    .addItem('Extract Links', 'appendLinksToDocument')
    .addItem('Extract People', 'appendPeopleToDocument')
    .addItem('Email to Person Chips', 'emailsToPersonChips')
    .addItem('go/linkify and extract all', 'goLinkifyAndExtractAll')
    .addToUi();
}

/**
 * Runs all available link tools in sequence.
 */
function goLinkifyAndExtractAll() {
  goLinkify();
  emailsToPersonChips();
  appendLinksToDocument();
  appendPeopleToDocument();
}

/**
 * Converts 'go/something' text patterns into clickable hyperlinks.
 * Transforms go/links into https://go/something URLs.
 */
function goLinkify() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const searchPattern = 'go/\\S+';
  let foundElement = body.findText(searchPattern);

  while (foundElement) {
    const textElement = foundElement.getElement().asText();
    const startOffset = foundElement.getStartOffset();
    const endOffset = foundElement.getEndOffsetInclusive();
    const matchedText = textElement.getText().substring(startOffset, endOffset + 1);
    const linkMatch = matchedText.match(/go\/(\S+)/);

    if (linkMatch && linkMatch[1]) {
      const linkUrl = 'https://' + matchedText;
      textElement.setLinkUrl(startOffset, endOffset, linkUrl);
    }

    foundElement = body.findText(searchPattern, foundElement);
  }
}

/**
 * Extracts all links from the document and appends them as a list at the end.
 * Groups links by type (hyperlink, richLink) and prevents duplicates.
 */
function appendLinksToDocument() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const links = getLinksFromBody(body);

  if (links.length === 0) {
    return;
  }
  body.appendParagraph('---');
  body.appendParagraph('Extracted Links:');
  links.forEach(function(link) {
    const paragraph = body.appendParagraph('');
    const displayText = link.text || link.url;
    const text = paragraph.appendText(displayText);
    text.setLinkUrl(link.url);
  });
}

/**
 * Extracts all people mentions from the document and appends them as a list at the end.
 * Creates mailto links for each person and prevents duplicates.
 */
function appendPeopleToDocument() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const people = getPeopleFromBody(body);

  if (people.length === 0) {
    return;
  }
  body.appendParagraph('---');
  body.appendParagraph('Extracted People:');
  people.forEach(function(person) {
    const paragraph = body.appendParagraph('');
    const text = paragraph.appendText(person.text);
    text.setLinkUrl(person.url);
  });
}

/**
 * Extracts all unique links from the document body.
 * @param {DocumentApp.Body} body - The document body to search for links
 * @return {Array} An array of link objects containing url, text, and type
 */
function getLinksFromBody(body) {
  const links = [];

  /**
   * Recursively searches for links in elements
   * @param {DocumentApp.Element} element - The element to search
   */
  function searchForLinks(element) {
    const numChildren = element.getNumChildren ? element.getNumChildren() : 0;

    for (let i = 0; i < numChildren; i++) {
      const child = element.getChild(i);
      const type = child.getType();

      if (type == DocumentApp.ElementType.TEXT) {
        const text = child.asText();
        const indices = text.getTextAttributeIndices();
        
        for (let j = 0; j < indices.length; j++) {
          const start = indices[j];
          const url = text.getLinkUrl(start);

          if (url && !links.some(link => link.url === url)) {
            links.push({ url: url, type: 'hyperlink' });
          }
        }
      } else if (type == DocumentApp.ElementType.RICH_LINK) {
        const richLink = child.asRichLink();
        const url = richLink.getUrl();
        const displayText = richLink.getUrl(); // using the Url instead of Title allows the link to be chipped
        
        if (url && !links.some(link => link.url === url)) {
          links.push({ url: url, text: displayText, type: 'richLink' });
        }
      } else {
        searchForLinks(child);
      }
    }
  }

  searchForLinks(body);
  return links;
}

/**
 * Extracts all unique people mentions from the document body.
 * @param {DocumentApp.Body} body - The document body to search for people mentions
 * @return {Array} An array of people objects containing url (mailto), text (display name), and type
 */
function getPeopleFromBody(body) {
  const people = [];

  /**
   * Recursively searches for people mentions in elements
   * @param {DocumentApp.Element} element - The element to search
   */
  function searchForPeople(element) {
    const numChildren = element.getNumChildren ? element.getNumChildren() : 0;

    for (let i = 0; i < numChildren; i++) {
      const child = element.getChild(i);
      const type = child.getType();

      if (type == DocumentApp.ElementType.PERSON) {
        const person = child.asPerson();
        const email = person.getEmail();
        const displayName = person.getName();

        if (email && !people.some(p => p.url === 'mailto:' + email)) {
          people.push({ url: 'mailto:' + email, text: displayName, type: 'mailto' });
        }
      } else {
        searchForPeople(child);
      }
    }
  }

  searchForPeople(body);
  return people;
}

/**
 * Converts plain email addresses in the document to Google Doc person chips.
 * Searches for valid email patterns and replaces them with proper person chips.
 */
function emailsToPersonChips() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  // Regular expression for finding email addresses
  // This pattern matches common email formats
  const emailPattern = '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b';
  let foundElement = body.findText(emailPattern);
  
  while (foundElement) {
    const textElement = foundElement.getElement().asText();
    const startOffset = foundElement.getStartOffset();
    const endOffset = foundElement.getEndOffsetInclusive();
    const email = textElement.getText().substring(startOffset, endOffset + 1);
    
    try {
      // Replace the text with a person chip
      // The insertPerson method takes the start position, end position, and email address
      textElement.insertPerson(startOffset, endOffset, email);
    } catch (e) {
      // Log any errors that occur during the conversion
      console.log('Error creating person chip for: ' + email + ' - ' + e.toString());
    }
    
    // Find the next email address after this one
    foundElement = body.findText(emailPattern, foundElement);
  }
}

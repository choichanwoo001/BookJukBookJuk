import coverAdultBecoming from '../assets/images/covers/cover-adult-becoming.png';
import coverKyoko from '../assets/images/covers/cover-kyoko.png';
import coverOnlyOnePerson from '../assets/images/covers/cover-only-one-person.png';
import coverWeDoNotPart from '../assets/images/covers/cover-we-do-not-part.png';

export const BOOK_COVERS = {
  'reading-1': coverAdultBecoming,
  'reading-3': coverOnlyOnePerson,
};

export const COMMUNITY_BOOK_COVERS = {
  교코: coverKyoko,
  '작별하지 않는다': coverWeDoNotPart,
};

export function getBookCover(bookId) {
  return BOOK_COVERS[bookId] ?? null;
}

export function getCommunityBookCover(title) {
  return COMMUNITY_BOOK_COVERS[title] ?? null;
}

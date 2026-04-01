import '@testing-library/jest-dom'

// jsdom은 scrollIntoView를 구현하지 않으므로 테스트 환경에서 no-op으로 대체한다.
// 실제 브라우저에서는 정상 동작한다.
window.HTMLElement.prototype.scrollIntoView = () => {}

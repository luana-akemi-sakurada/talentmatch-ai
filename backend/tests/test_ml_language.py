from unittest.mock import patch
import ml_language


def test_english_unchanged():
    with patch('ml_language.identify', return_value='en'), patch('ml_language.translate_portuguese') as translator:
        text = 'I develop software with Python and React.'
        assert ml_language.to_english(text) == text
        translator.assert_not_called()


def test_portuguese_routed_without_mutating_original():
    original = 'Desenvolvo sistemas com Python e React.'
    with patch('ml_language.identify', return_value='pt'), patch('ml_language.translate_portuguese', return_value='I develop systems with Python and React.') as translator:
        result = ml_language.to_english(original)
        assert result == 'I develop systems with Python and React.'
        assert original == 'Desenvolvo sistemas com Python e React.'
        translator.assert_called_once_with(original)


def test_empty_input_does_not_load_models():
    with patch('ml_language._translator') as translator:
        assert ml_language.to_english('') == ''
        translator.assert_not_called()


def test_short_technical_term_unchanged():
    assert ml_language.identify('React TypeScript') == 'und'

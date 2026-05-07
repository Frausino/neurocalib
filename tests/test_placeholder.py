"""Placeholder S1 — verifica que o pacote é importável.

Remover quando os primeiros testes reais de domain/ forem criados em S3.
"""


def test_package_importable() -> None:
    """Verifica importação do pacote raiz."""
    import bci_calib  # noqa: PLC0415

    assert bci_calib is not None

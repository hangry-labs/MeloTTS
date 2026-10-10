import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

from melo.model_registry import BERT_MODEL_REVISIONS, load_bert_tokenizer


class BertTokenizerLoadingTests(unittest.TestCase):
    @patch.dict(os.environ, {"MELOTTS_LOCAL_FILES_ONLY": "1"})
    def test_local_only_loading_uses_cached_snapshot_path(self):
        model_id = "bert-base-multilingual-uncased"
        from_pretrained = Mock()
        snapshot_download = Mock()
        snapshot_download.return_value = "/cache/multilingual-snapshot"
        transformers = types.ModuleType("transformers")
        transformers.AutoTokenizer = types.SimpleNamespace(
            from_pretrained=from_pretrained
        )
        huggingface_hub = types.ModuleType("huggingface_hub")
        huggingface_hub.snapshot_download = snapshot_download

        with patch.dict(
            sys.modules,
            {"transformers": transformers, "huggingface_hub": huggingface_hub},
        ):
            tokenizer = load_bert_tokenizer(model_id)

        self.assertIs(tokenizer, from_pretrained.return_value)
        snapshot_download.assert_called_once_with(
            repo_id=model_id,
            revision=BERT_MODEL_REVISIONS[model_id],
            local_files_only=True,
        )
        from_pretrained.assert_called_once_with(
            "/cache/multilingual-snapshot",
            local_files_only=True,
            fix_mistral_regex=False,
        )

    @patch.dict(os.environ, {"MELOTTS_LOCAL_FILES_ONLY": "0"})
    def test_online_loading_keeps_pinned_repository_revision(self):
        model_id = "bert-base-multilingual-uncased"
        from_pretrained = Mock()
        transformers = types.ModuleType("transformers")
        transformers.AutoTokenizer = types.SimpleNamespace(
            from_pretrained=from_pretrained
        )

        with patch.dict(sys.modules, {"transformers": transformers}):
            tokenizer = load_bert_tokenizer(model_id)

        self.assertIs(tokenizer, from_pretrained.return_value)
        from_pretrained.assert_called_once_with(
            model_id,
            local_files_only=False,
            revision=BERT_MODEL_REVISIONS[model_id],
        )


if __name__ == "__main__":
    unittest.main()

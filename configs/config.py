import os

# DIR_PATH=os.path.dirname(os.path.realpath(__file__))
DIR_PATH=os.getcwd() 
# Query units
QUNITS_FILE='/output/{0}/{0}_{1}_qunits.json'
QUNITS_DEBUG_FILE='/output/{0}/{0}_{1}_qunits_debug.json'
QUNITS_SET_COVER_FILE='/output/{0}/{0}_{1}_qunits_set_cover.json'
QUNITS_SET_COVER_MINUS_FILE='/output/{0}/{0}_{1}_qunits_set_generated_cover.json'
# Generalization
TRIAL_KNOB=1000
# Retrieval mdel
RETRIEVAL_MODEL_EMBEDDING_DIMENSION = 768
RETRIEVAL_EMBEDDING_MODEL_NAME = 'all-mpnet-base-v2'
SEMSIMILARITY_TRIPLE_DATA_GZ_FILE = '/output/{0}/sentence_embedder/sentence_emb.tsv.gz'
SEMSIMILARITY_TRIPLE_DATA_FINETUNE_GZ_FILE='/output/spider/sentence_embedder/spider_sentence_emb_finetune.tsv.gz'
RETRIEVAL_MODEL_DIR='/output/{0}/sentence_embedder'
CANDIDATE_NUM=100
# Default lr is 2e-5 
RETRIVIAL_MODEL_LEARNING_RATE=5e-6
# Re-ranker
RERANKER_EMBEDDING_MODEL_NAME='roberta-base'
RERANKER_MODEL_NAME='bertpooler'
RERANKER_TRAIN_DATA_FILE='/output/{0}/reranker/reranker_train.json'
RERANKER_DEV_DATA_FILE='/output/{0}/reranker/reranker_dev.json'
RERANKER_MODEL_DIR='/output/{0}/reranker'
RERANKER_TEST_DATA_FILE='/output/{0}/reranker/reranker_test.json'
RERANKER_TRAIN_FINETUNE_DATA_FILE='/output/spider/reranker/spider_reranker_train_finetune.json'
RERANKER_DEV_FINETUNE_DATA_FILE='/output/spider/reranker/spider_reranker_dev_finetune.json'
RERANKER_CONFIG_FILE='/allenmodels/train_configs/ranker_pair_100.jsonnet'
RERANKER_FINETUNE_CONFIG_FILE='/train_configs/ranker_pair_finetune.jsonnet'
RERANKER_MODEL_OUTPUT_FILE='/output/spider/reranker/output.txt'
# Model output postprocess
POSTPROCESS_OUTPUT_FILE='/model_output_postprocess/outputs/{0}/{0}_output.json'
# Synthesis serialization
SERIALIZE_DATA_DIR='/output/{0}/serialization'
# SQL gen time limit
TIME_LIMIT_PRE_SQL=5  # seconds generate more than one sql
# Output
PRED_FILE='/output/spider/pred.txt'
OUTPUT_DIR_SPIDER='/output/spider'
OUTPUT_DIR_RERANKER='/output/{0}/reranker'
RERANKER_INPUT_FILE_NAME='test.json'
PRED_FILE_NAME='pred.txt'
PRED_SQL_FILE_NAME='pred_sql.txt'
PRED_TOPK_FILE_NAME='pred_topk.txt'
PRED_SQL_TOPK_FILE_NAME='pred_sql_topk.txt'
CANDIDATE_MISS_FILE_NAME='candidategen_miss.txt'
SQL_MISS_FILE_NAME='sqlgen_miss.txt'
RERANKER_MISS_FILE_NAME='reranker_miss.txt'
RERANKER_MISS_TOPK_FILE_NAME='reranker_miss_topk.txt'
VALUE_FILTERED_TOPK_FILE_NAME='value_filtered_miss_topk.txt'
# Misc.
MODEL_TAR_GZ='model.tar.gz'
# re-generate serialized dialects 
# (True to make any change in Dialect Builder gets effected)
REWRITE_FLAG=False
# Overwrite flag for the serialized generation data 
# (True to make any change in SQLGenV2 gets effected)
OVERWRITE_FLAG=False
MODE='test'
DEBUG=True
TOP_NUM=10
# Toggle to enable/disable using annotations during dialect generation
USE_ANNOTATION=False

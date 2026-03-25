from pydantic import ValidationError
from config.settings import QuickBaseConfig
from utils.logger import ExecutionLogger
from pipeline.orchestrator import TestPipeline

if __name__ == "__main__":
    try:
        config = QuickBaseConfig()
        with ExecutionLogger('scheduledProcessedLog.csv') as logger:
            pipeline = TestPipeline(config, logger)
            pipeline.run()
    except ValidationError as e:
        print(f"Configuration Validation Error: {e}")

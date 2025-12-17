#!/usr/bin/env python3
"""
Validate dbt metadata completeness for models and columns
"""
import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set

class MetadataValidator:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.models_dir = self.project_dir / "models"
        self.errors = []
        self.warnings = []
        
    def find_schema_files(self) -> List[Path]:
        """Find all schema.yml files in models directory"""
        return list(self.models_dir.rglob("*.yml")) + list(self.models_dir.rglob("*.yaml"))
    
    def find_sql_files(self) -> List[Path]:
        """Find all SQL model files"""
        return list(self.models_dir.rglob("*.sql"))
    
    def load_schema_file(self, file_path: Path) -> Dict:
        """Load and parse a schema YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.errors.append(f"❌ Error reading {file_path}: {e}")
            return {}
    
    def validate_model_documentation(self):
        """Validate that all models have descriptions"""
        print("🔍 Validating model descriptions...")
        
        schema_files = self.find_schema_files()
        sql_files = self.find_sql_files()
        
        # Get all model names from SQL files
        model_names = {f.stem for f in sql_files}
        
        # Get documented models from schema files
        documented_models = {}
        for schema_file in schema_files:
            schema = self.load_schema_file(schema_file)
            
            if 'models' in schema:
                for model in schema['models']:
                    model_name = model.get('name')
                    description = model.get('description', '').strip()
                    
                    documented_models[model_name] = {
                        'description': description,
                        'file': schema_file
                    }
        
        # Check for undocumented models
        for model_name in model_names:
            if model_name not in documented_models:
                self.errors.append(
                    f"❌ Model '{model_name}' has no schema documentation"
                )
            elif not documented_models[model_name]['description']:
                self.errors.append(
                    f"❌ Model '{model_name}' has empty description in {documented_models[model_name]['file']}"
                )
            elif len(documented_models[model_name]['description']) < 10:
                self.warnings.append(
                    f"⚠️  Model '{model_name}' has very short description (< 10 chars)"
                )
    
    def validate_column_documentation(self):
        """Validate that all columns have descriptions"""
        print("🔍 Validating column descriptions...")
        
        schema_files = self.find_schema_files()
        
        for schema_file in schema_files:
            schema = self.load_schema_file(schema_file)
            
            if 'models' in schema:
                for model in schema['models']:
                    model_name = model.get('name')
                    columns = model.get('columns', [])
                    
                    if not columns:
                        self.warnings.append(
                            f"⚠️  Model '{model_name}' has no columns documented in {schema_file}"
                        )
                        continue
                    
                    for column in columns:
                        col_name = column.get('name')
                        description = column.get('description', '').strip()
                        
                        if not description:
                            self.errors.append(
                                f"❌ Column '{model_name}.{col_name}' has no description in {schema_file}"
                            )
                        elif len(description) < 5:
                            self.warnings.append(
                                f"⚠️  Column '{model_name}.{col_name}' has very short description (< 5 chars)"
                            )
    
    def validate_tests(self):
        """Validate that critical columns have tests"""
        print("🔍 Validating column tests...")
        
        schema_files = self.find_schema_files()
        
        for schema_file in schema_files:
            schema = self.load_schema_file(schema_file)
            
            if 'models' in schema:
                for model in schema['models']:
                    model_name = model.get('name')
                    columns = model.get('columns', [])
                    
                    for column in columns:
                        col_name = column.get('name')
                        tests = column.get('tests', [])
                        
                        # Check if ID columns have unique/not_null tests
                        if 'id' in col_name.lower():
                            test_types = []
                            for test in tests:
                                if isinstance(test, str):
                                    test_types.append(test)
                                elif isinstance(test, dict):
                                    test_types.extend(test.keys())
                            
                            if 'unique' not in test_types:
                                self.warnings.append(
                                    f"⚠️  ID column '{model_name}.{col_name}' should have 'unique' test"
                                )
                            if 'not_null' not in test_types:
                                self.warnings.append(
                                    f"⚠️  ID column '{model_name}.{col_name}' should have 'not_null' test"
                                )
    
    def validate_tags(self):
        """Validate that models have appropriate tags"""
        print("🔍 Validating model tags...")
        
        schema_files = self.find_schema_files()
        
        for schema_file in schema_files:
            schema = self.load_schema_file(schema_file)
            
            if 'models' in schema:
                for model in schema['models']:
                    model_name = model.get('name')
                    tags = model.get('tags', [])
                    
                    if not tags:
                        self.warnings.append(
                            f"⚠️  Model '{model_name}' has no tags defined"
                        )
    
    def generate_report(self) -> bool:
        """Generate validation report and return success status"""
        print("\n" + "="*60)
        print("📋 VALIDATION REPORT")
        print("="*60 + "\n")
        
        # Write results to file for GitHub Actions
        report_lines = []
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            report_lines.append(f"### ❌ Errors ({len(self.errors)})\n")
            for error in self.errors:
                print(f"  {error}")
                report_lines.append(f"- {error}\n")
            report_lines.append("\n")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            report_lines.append(f"### ⚠️ Warnings ({len(self.warnings)})\n")
            for warning in self.warnings:
                print(f"  {warning}")
                report_lines.append(f"- {warning}\n")
            report_lines.append("\n")
        
        if not self.errors and not self.warnings:
            print("✅ All validation checks passed!")
            report_lines.append("### ✅ All validation checks passed!\n")
        
        # Write report for GitHub Actions
        report_path = Path(".github/validation_results.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.writelines(report_lines)
        
        # Return success if no errors (warnings are OK)
        return len(self.errors) == 0
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        self.validate_model_documentation()
        self.validate_column_documentation()
        self.validate_tests()
        self.validate_tags()
        
        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(description='Validate dbt metadata completeness')
    parser.add_argument('--project-dir', required=True, help='Path to dbt project directory')
    args = parser.parse_args()
    
    validator = MetadataValidator(args.project_dir)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

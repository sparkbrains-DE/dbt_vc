#!/usr/bin/env python3
"""
Check for breaking schema changes in dbt models
"""
import os
import sys
import yaml
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Set

class SchemaChangeChecker:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.models_dir = self.project_dir / "models"
        self.breaking_changes = []
        self.non_breaking_changes = []
        
    def get_changed_files(self) -> List[str]:
        """Get list of changed files in this PR"""
        try:
            # Compare with main branch
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'origin/main...HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return [f for f in result.stdout.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            print("⚠️  Could not determine changed files")
            return []
    
    def load_schema_file(self, file_path: Path) -> Dict:
        """Load and parse a schema YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return {}
    
    def get_schema_from_git(self, file_path: str, ref: str = 'origin/main') -> Dict:
        """Get schema file content from a git reference"""
        try:
            result = subprocess.run(
                ['git', 'show', f'{ref}:{file_path}'],
                capture_output=True,
                text=True,
                check=True
            )
            return yaml.safe_load(result.stdout) or {}
        except (subprocess.CalledProcessError, yaml.YAMLError):
            return {}
    
    def check_column_removals(self, model_name: str, old_columns: List[str], new_columns: List[str]):
        """Check if columns were removed (breaking change)"""
        removed_columns = set(old_columns) - set(new_columns)
        
        if removed_columns:
            self.breaking_changes.append(
                f"🚨 BREAKING: Model '{model_name}' removed columns: {', '.join(removed_columns)}"
            )
    
    def check_column_additions(self, model_name: str, old_columns: List[str], new_columns: List[str]):
        """Check if columns were added (non-breaking change)"""
        added_columns = set(new_columns) - set(old_columns)
        
        if added_columns:
            self.non_breaking_changes.append(
                f"✅ Model '{model_name}' added columns: {', '.join(added_columns)}"
            )
    
    def check_schema_changes(self):
        """Check for schema changes in modified files"""
        print("🔍 Checking for schema changes...")
        
        changed_files = self.get_changed_files()
        schema_files = [f for f in changed_files if f.endswith(('.yml', '.yaml')) and 'models' in f]
        
        for schema_file in schema_files:
            print(f"\n📄 Checking {schema_file}...")
            
            # Get current version
            current_schema = self.load_schema_file(Path(schema_file))
            
            # Get main branch version
            main_schema = self.get_schema_from_git(schema_file)
            
            if not main_schema:
                print(f"  ℹ️  New schema file (no comparison needed)")
                continue
            
            # Compare models
            current_models = {m['name']: m for m in current_schema.get('models', [])}
            main_models = {m['name']: m for m in main_schema.get('models', [])}
            
            for model_name in set(current_models.keys()) | set(main_models.keys()):
                if model_name not in main_models:
                    print(f"  ✅ New model: {model_name}")
                    continue
                
                if model_name not in current_models:
                    self.breaking_changes.append(
                        f"🚨 BREAKING: Model '{model_name}' was removed"
                    )
                    continue
                
                # Compare columns
                old_columns = [c['name'] for c in main_models[model_name].get('columns', [])]
                new_columns = [c['name'] for c in current_models[model_name].get('columns', [])]
                
                self.check_column_removals(model_name, old_columns, new_columns)
                self.check_column_additions(model_name, old_columns, new_columns)
    
    def generate_report(self) -> bool:
        """Generate schema change report"""
        print("\n" + "="*60)
        print("📋 SCHEMA CHANGE REPORT")
        print("="*60 + "\n")
        
        if self.breaking_changes:
            print(f"🚨 BREAKING CHANGES ({len(self.breaking_changes)}):")
            for change in self.breaking_changes:
                print(f"  {change}")
            print("\n⚠️  Breaking changes detected! Please ensure:")
            print("  - Downstream dependencies are updated")
            print("  - Migration plan is documented")
            print("  - Stakeholders are notified")
        
        if self.non_breaking_changes:
            print(f"\n✅ NON-BREAKING CHANGES ({len(self.non_breaking_changes)}):")
            for change in self.non_breaking_changes:
                print(f"  {change}")
        
        if not self.breaking_changes and not self.non_breaking_changes:
            print("ℹ️  No schema changes detected")
        
        # Breaking changes should not fail the build, just warn
        return True
    
    def run_checks(self) -> bool:
        """Run all schema change checks"""
        self.check_schema_changes()
        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(description='Check for schema changes in dbt models')
    parser.add_argument('--project-dir', required=True, help='Path to dbt project directory')
    args = parser.parse_args()
    
    checker = SchemaChangeChecker(args.project_dir)
    success = checker.run_checks()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

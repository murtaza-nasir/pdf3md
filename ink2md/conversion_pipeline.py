#!/usr/bin/env python3
"""
Ink2MD Conversion Pipeline
Based on PDF3MD by Murtaza Nsair
Original: https://github.com/murtaza-nasir/pdf3md

Copyright (C) 2025 Ink2MD Contributors
Copyright (C) 2024 Murtaza Nsair (original PDF3MD)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import time
import logging
import traceback
import pymupdf4llm
import pymupdf
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from models import ConversionStatus
from config_manager import ConfigManager
from database import DatabaseManager
from ai_services import AIServiceFactory
from prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ConversionPipeline:
    """Enhanced conversion pipeline with AI integration and comprehensive error handling."""
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager,
                 ai_factory: AIServiceFactory, progress_callback: Optional[Callable] = None):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.ai_factory = ai_factory
        self.progress_callback = progress_callback
        self.prompt_manager = PromptManager(config_manager)
        
    def update_progress(self, conversion_id: str, progress: int, stage: str, **kwargs):
        """Update conversion progress and call callback if provided."""
        if self.progress_callback:
            self.progress_callback(conversion_id, progress, stage, **kwargs)
        logger.debug(f"Conversion {conversion_id}: {progress}% - {stage}")
    
    def convert_pdf(self, temp_path: str, conversion_id: str, filename: str) -> Dict[str, Any]:
        """
        Enhanced PDF conversion pipeline with AI integration.
        
        Pipeline Steps:
        1. Database logging (status: 'queued')
        2. PDF preprocessing (metadata extraction)
        3. HTR processing with configured provider (if enabled)
        4. Raw text assembly
        5. AI formatting/refinement with configured provider (if enabled)
        6. Output file naming (configurable patterns)
        7. Save final markdown
        8. Database update (status: 'completed'/'failed')
        9. Cleanup temporary files
        """
        try:
            # Step 1: Initialize and create database record
            logger.info(f"Starting conversion pipeline for {filename} (ID: {conversion_id})")
            
            # Get PDF metadata
            doc = pymupdf.open(temp_path)
            total_pages = len(doc)
            file_size = os.path.getsize(temp_path)
            doc.close()
            
            # Create database record
            try:
                self.db_manager.create_conversion_record(
                    conversion_id=conversion_id,
                    original_filename=filename,
                    file_size=file_size,
                    page_count=total_pages
                )
                logger.info(f"Created database record for conversion {conversion_id}")
            except Exception as db_error:
                logger.error(f"Failed to create database record: {db_error}")
                # Continue with conversion even if database logging fails
            
            self.update_progress(conversion_id, 5, "Initializing conversion...", 
                               total_pages=total_pages, filename=filename, file_size=file_size)
            
            # Update database status to processing
            try:
                self.db_manager.update_conversion_status(
                    conversion_id=conversion_id,
                    status='processing'
                )
            except Exception as db_error:
                logger.error(f"Failed to update database status: {db_error}")
            
            # Step 2: Check for VLM processing first
            vlm_markdown = self._process_with_vlm(temp_path, conversion_id, filename)
            
            if vlm_markdown:
                # VLM processing successful, use that result
                markdown_content = vlm_markdown
                self.update_progress(conversion_id, 85, "VLM processing complete")
            else:
                # Fallback to traditional pipeline
                self.update_progress(conversion_id, 10, "Extracting text from PDF...")
                
                # Basic PDF to markdown conversion using pymupdf4llm
                markdown_content = pymupdf4llm.to_markdown(temp_path)
                
                self.update_progress(conversion_id, 40, "Basic text extraction complete")
                
                # Step 3: AI Enhancement (if configured)
                formatting_provider_id = self.config_manager.get_setting('active_services.formatting_provider_id')
                
                if formatting_provider_id:
                    try:
                        self.update_progress(conversion_id, 50, f"Enhancing with AI ({formatting_provider_id})...")
                        
                        # Get AI service
                        ai_service = self.ai_factory.get_service(formatting_provider_id)
                        
                        if ai_service and ai_service.is_available():
                            self.update_progress(conversion_id, 70, "Refining markdown formatting with AI...")
                            
                            # Format the markdown using AI with prompt manager
                            enhanced_markdown = self._enhance_markdown_with_ai(ai_service, markdown_content, filename)
                            if enhanced_markdown:
                                markdown_content = enhanced_markdown
                                self.update_progress(conversion_id, 85, "AI enhancement complete")
                            else:
                                self.update_progress(conversion_id, 85, "AI enhancement skipped (using original)")
                        else:
                            logger.warning(f"AI service {formatting_provider_id} not available")
                            self.update_progress(conversion_id, 85, "AI service not available, using original text")
                            
                    except Exception as ai_error:
                        logger.error(f"AI enhancement failed: {ai_error}")
                        self.update_progress(conversion_id, 85, "AI enhancement failed, using original text")
                        # Continue with original markdown content
                else:
                    self.update_progress(conversion_id, 85, "AI enhancement disabled, using original text")
            
            # Step 6: Output file naming
            self.update_progress(conversion_id, 90, "Finalizing output...")
            
            output_pattern = self.config_manager.get_setting('app_settings.default_output_pattern', 'YYYY-MM-DD-[OriginalFileName].md')
            timestamp_str = datetime.now().strftime('%Y-%m-%d')
            base_filename = os.path.splitext(filename)[0]
            output_filename = output_pattern.replace('YYYY-MM-DD', timestamp_str).replace('[OriginalFileName]', base_filename)
            
            # Step 7: Format file size helper
            def format_file_size(size_bytes):
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            
            # Step 8: Create result
            vlm_provider_id = self.config_manager.get_setting('active_services.vlm_provider_id')
            formatting_provider_id = self.config_manager.get_setting('active_services.formatting_provider_id')
            
            result = {
                'markdown': markdown_content,
                'filename': filename,
                'fileSize': format_file_size(file_size),
                'pageCount': total_pages,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'ai_enhanced': bool(vlm_markdown or formatting_provider_id),
                'processing_method': 'vlm' if vlm_markdown else 'traditional',
                'vlm_provider': vlm_provider_id if vlm_markdown else None,
                'formatting_provider': formatting_provider_id if not vlm_markdown and formatting_provider_id else None,
                'prompt_templates_used': self._get_used_prompt_templates(vlm_markdown, filename)
            }
            
            self.update_progress(conversion_id, 95, "Conversion complete!", status='completed', result=result)
            
            # Step 9: Update database with completion
            try:
                self.db_manager.update_conversion_status(
                    conversion_id=conversion_id,
                    status='completed',
                    output_filename=output_filename,
                    final_markdown_path=f"/app/output_markdown/{output_filename}"
                )
                logger.info(f"Updated database record for completed conversion {conversion_id}")
            except Exception as db_error:
                logger.error(f"Failed to update database on completion: {db_error}")
            
            self.update_progress(conversion_id, 100, "Pipeline complete!")
            logger.info(f"Conversion pipeline completed successfully for {filename}")
            
            return result
            
        except Exception as e:
            logger.error(f'Conversion pipeline error: {str(e)}')
            logger.error(traceback.format_exc())
            
            # Update database with error
            try:
                self.db_manager.update_conversion_status(
                    conversion_id=conversion_id,
                    status='failed',
                    error_message=str(e)
                )
                logger.info(f"Updated database record for failed conversion {conversion_id}")
            except Exception as db_error:
                logger.error(f"Failed to update database on error: {db_error}")
            
            # Update progress with error
            if self.progress_callback:
                self.progress_callback(conversion_id, 0, f'Error: {str(e)}', status='error', error=str(e))
            
            raise e
    
    def _enhance_markdown_with_ai(self, ai_service, markdown_content: str, filename: str) -> Optional[str]:
        """Enhance markdown content using AI service with prompt templates."""
        try:
            # Determine document type from filename
            document_type = self._determine_document_type(filename)
            
            # Get appropriate prompt template
            prompt_template = f"formatting_{document_type}"
            
            # Use the AI service to enhance the content with prompt manager
            if hasattr(ai_service, 'format_markdown'):
                enhanced_content = ai_service.format_markdown(
                    markdown_content,
                    prompt_manager=self.prompt_manager,
                    prompt_template=prompt_template,
                    filename=filename,
                    document_type=document_type
                )
            else:
                # Fallback for services without format_markdown method
                prompt = self.prompt_manager.get_prompt(
                    prompt_template,
                    content=markdown_content,
                    filename=filename,
                    document_type=document_type
                )
                enhanced_content = ai_service.generate_text(prompt)
            
            if enhanced_content and len(enhanced_content.strip()) > 0:
                logger.info(f"Successfully enhanced markdown content using AI with {prompt_template} template")
                return enhanced_content.strip()
            else:
                logger.warning("AI service returned empty content")
                return None
                
        except Exception as e:
            logger.error(f"Failed to enhance markdown with AI: {e}")
            return None
    
    def _determine_document_type(self, filename: str) -> str:
        """Determine document type from filename for appropriate prompt selection."""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ['academic', 'paper', 'journal', 'research', 'thesis']):
            return 'academic'
        elif any(keyword in filename_lower for keyword in ['note', 'notes', 'meeting', 'memo']):
            return 'notes'
        elif any(keyword in filename_lower for keyword in ['form', 'application', 'survey']):
            return 'forms'
        else:
            return 'clean'
    
    def _process_with_vlm(self, temp_path: str, conversion_id: str, filename: str) -> Optional[str]:
        """
        Process PDF directly with Vision-Language Model for end-to-end conversion.
        
        Args:
            temp_path: Path to the PDF file
            conversion_id: Conversion ID for progress tracking
            filename: Original filename
            
        Returns:
            Optional[str]: Generated markdown content or None if failed
        """
        try:
            # Get VLM service
            vlm_provider_id = self.config_manager.get_setting('active_services.vlm_provider_id')
            if not vlm_provider_id:
                logger.info("No VLM provider configured, skipping VLM processing")
                return None
            
            vlm_service = self.ai_factory.get_service(vlm_provider_id)
            if not vlm_service or not vlm_service.supports_capability('vlm_direct'):
                logger.info(f"VLM service {vlm_provider_id} not available or doesn't support VLM processing")
                return None
            
            self.update_progress(conversion_id, 20, "Processing with Vision-Language Model...")
            
            # Extract pages as images
            doc = pymupdf.open(temp_path)
            markdown_pages = []
            
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x scaling for better quality
                    img_data = pix.tobytes("png")
                    
                    # Save temporary image
                    temp_img_path = f"/tmp/page_{conversion_id}_{page_num}.png"
                    with open(temp_img_path, "wb") as img_file:
                        img_file.write(img_data)
                    
                    # Determine document type and get appropriate prompt
                    document_type = self._determine_document_type(filename)
                    prompt_template = f"vlm_{document_type}"
                    
                    prompt = self.prompt_manager.get_prompt(
                        prompt_template,
                        filename=filename,
                        page_number=page_num + 1,
                        total_pages=len(doc),
                        document_type=document_type
                    )
                    
                    # Process with VLM
                    page_markdown = vlm_service.process_with_vlm(
                        temp_img_path,
                        prompt,
                        prompt_manager=self.prompt_manager,
                        document_type=document_type
                    )
                    
                    if page_markdown:
                        markdown_pages.append(page_markdown)
                    
                    # Clean up temporary image
                    try:
                        os.remove(temp_img_path)
                    except:
                        pass
                    
                    # Update progress
                    progress = 20 + (60 * (page_num + 1) / len(doc))
                    self.update_progress(conversion_id, int(progress), f"Processed page {page_num + 1}/{len(doc)} with VLM")
                    
                except Exception as page_error:
                    logger.error(f"Failed to process page {page_num} with VLM: {page_error}")
                    continue
            
            doc.close()
            
            if markdown_pages:
                # Combine pages with appropriate separators
                combined_markdown = "\n\n---\n\n".join(markdown_pages)
                logger.info(f"Successfully processed {len(markdown_pages)} pages with VLM")
                return combined_markdown
            else:
                logger.warning("No pages were successfully processed with VLM")
                return None
                
        except Exception as e:
            logger.error(f"VLM processing failed: {e}")
            return None
    
    def retry_conversion(self, conversion_id: str) -> Dict[str, Any]:
        """Retry a failed conversion using exponential backoff."""
        try:
            # Get conversion record from database
            record = self.db_manager.get_conversion_by_id(conversion_id)
            if not record:
                raise ValueError(f"Conversion record {conversion_id} not found")
            
            # Check if retry is allowed
            max_retries = self.config_manager.get_setting('app_settings.max_retries', 3)
            if record.retry_count >= max_retries:
                raise ValueError(f"Maximum retries ({max_retries}) exceeded for conversion {conversion_id}")
            
            # Calculate backoff delay
            backoff_delay = min(2 ** record.retry_count, 60)  # Max 60 seconds
            logger.info(f"Retrying conversion {conversion_id} after {backoff_delay}s delay (attempt {record.retry_count + 1})")
            
            time.sleep(backoff_delay)
            
            # Update retry count
            self.db_manager.increment_retry_count(conversion_id)
            
            # Reset status to processing
            self.db_manager.update_conversion_status(conversion_id, 'processing')
            
            # Note: The actual file path and retry logic would need to be implemented
            # based on how temporary files are managed
            logger.info(f"Retry conversion {conversion_id} initiated")
            
            return {"status": "retry_initiated", "conversion_id": conversion_id}
            
        except Exception as e:
            logger.error(f"Failed to retry conversion {conversion_id}: {e}")
            raise e
    
    def _get_used_prompt_templates(self, vlm_used: bool, filename: str) -> List[str]:
        """Get list of prompt templates that were used in processing."""
        templates = []
        
        if vlm_used:
            document_type = self._determine_document_type(filename)
            templates.append(f"vlm_{document_type}")
        else:
            document_type = self._determine_document_type(filename)
            templates.append(f"formatting_{document_type}")
        
        return templates
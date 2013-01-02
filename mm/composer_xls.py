from composer_base import ComposerBase
import lib.xlwt_0_7_2 as xlwt
from lib.font_data.core import get_string_width 
import logging
import StringIO
import model_base
import style_base

log = logging.getLogger(__name__)


def get_string_width_from_style(char_string, style):
    point_size = style.font.height / 0x14 # convert back to points 
    font_name = style.font.name
    return int(get_string_width(font_name, point_size, char_string) * 50)

class styleXLS(style_base.StyleBase):

    font_name = "Times New Roman"
    is_bold = False
    font_points = 12
    text_align = xlwt.Alignment()
    pattern = xlwt.Pattern()
    border = xlwt.Borders()


class ComposerXLS(ComposerBase):


    def convert_style(self, stylestr):
       in_style = styleXLS()
       in_style.style_from_string(stylestr)

       style =  xlwt.XFStyle()
       fnt1 = xlwt.Font()
       fnt1.name = in_style.font_name
       fnt1.bold = in_style.is_bold
       fnt1.height = in_style.font_points*0x14
       style.font = fnt1
       style.alignment = in_style.text_align
       style.pattern = in_style.pattern
       style.borders = in_style.border

       return style

    def cell_to_value(self, cell):
        
        style = self.convert_style(self.document.config.row_styles[0])
        
        if type(cell) == model_base.HeaderFieldType:
            style = self.convert_style(self.document.config.header_style)
            return cell.data, style

        elif type(cell) in (model_base.IntFieldType, model_base.StringFieldType):
            return cell.data, style

        elif type(cell) == model_base.DateTimeFieldType:
            style.num_format_str = self.document.config.get('datetime_format', 'M/D/YY h:mm')
            return cell.data, style
        elif type(cell) == model_base.DateFieldType:
            style.num_format_str = self.document.config.get('date_format', 'M/D/YY')
            return cell.data, style
        
        return "", style


    def start_new_row(self, id):
        pass


    def end_row(self, id):
        pass

    def write_cell(self, row_id, col_id, cell):
        
        value, style = self.cell_to_value(cell)
        self.sheet.write(row_id, col_id, value, style)
        self.done_write_cell(row_id, col_id, cell, value, style)

    def done_write_cell(self, row_id, col_id, cell, value, style):
         if self.document.config.get('adjust_all_col_width', False):    
             if type(cell) == model_base.StringFieldType:
                current_width = self.sheet.col_width(col_id)
                log.info("current width is %s" % current_width)
                new_width = get_string_width_from_style(value, style)
                if new_width > current_width:
                    log.info("setting col #%s form width %s to %s" % (col_id,current_width,new_width))
                    col = self.sheet.col(col_id)
                    col.width = new_width
             elif type(cell) == model_base.DateTimeFieldType:
                current_width = self.sheet.col_width(col_id)
                log.info("current width is %s" % current_width)
                new_width = 5000 #todo: different date formats
                if new_width > current_width:
                    log.info("setting col #%s form width %s to %s" % (col_id,current_width,new_width))
                    col = self.sheet.col(col_id)
                    col.width = new_width
                 
                

    def set_option(self, key):
       
        val = getattr(self.document.config,key)
        if key == 'freeze_col' and val and val >0:
            self.sheet.panes_frozen = True
            self.sheet.vert_split_pos = val
         
        elif key == 'freeze_row' and val and val >0:
            self.sheet.panes_frozen = True
            self.sheet.horz_split_pos = val

        else:

            log.info("Nothing to be done for %s" % key) 
    
            return
        log.info("Set option %s" % key) 



    def run(self):
           
        self.w = xlwt.Workbook()        
        self.sheet = self.w.add_sheet('Sheet 1')
        if self.document.config.headers:
            self.write_header()
        self.iterate_grid()
        self.finish()       
         
        # write the file to string
        output = StringIO.StringIO() 
        self.w.save(output)
        contents = output.getvalue()
        output.close()

        return contents






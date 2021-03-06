import re


class PreProcessor:
    def __init__(self):
        self.dev_code = """
    event Log(uint);
    event LogInt(int);
    event LogUintArray256(uint[256]);
    event LogAddress(address);
    event LogBytes32(bytes32);
    event LogBytes(bytes);
    event LogByte(bytes1);
    event LogBool(bool);
    """

    @staticmethod
    def find_macro(code):
        return re.search(r'macro:(.*?);', code)

    @staticmethod
    def find_scope_end(code, start_pos):
        brackets_counter = 0
        index = 0
        for index, char in enumerate(code[start_pos:]):
            if char == "{":
                brackets_counter += 1
            elif char == "}":
                brackets_counter -= 1
            if brackets_counter < 0:
                break
        return start_pos + index

    def resolve_macros(self, code):
        # replace macros
        macro = self.find_macro(code)
        while macro:
            token, solidity_code = [x.strip() for x in macro.group()[6:-1].split("=")]
            scope_end = self.find_scope_end(code, macro.end())
            new_code = code[macro.end():scope_end].replace(token, solidity_code)
            code = code[:macro.start()] + new_code + code[scope_end:]
            macro = self.find_macro(code)
        return code

    @staticmethod
    def resolve_imports(code, file_name, contract_dir):
        imported_codes = [file_name]
        while len(re.findall(r'import "(\S*)";', code)):
            for file_name in re.findall(r'import "(\S*)";', code):
                if file_name not in imported_codes:
                    imported_code = open(contract_dir + file_name).read()
                    imported_codes.append(file_name)
                else:
                    imported_code = ""
                code = code.replace('import "{}";'.format(file_name), imported_code)
        return code

    @staticmethod
    def insert_addresses(code, replace_dict):
        for placeholder, address in replace_dict.iteritems():
            code = code.replace("{{%s}}" % placeholder, address)
        return code

    def process(self, file_name, add_dev_code=False, contract_dir="", addresses=None, replace_unknown_addresses=False):
        code = open(contract_dir + file_name).read()
        # resolve imports
        code = self.resolve_imports(code, file_name, contract_dir)
        # resolve macros
        code = self.resolve_macros(code)
        # insert admin code
        code = code.replace("{{dev_code}}", self.dev_code if add_dev_code else "")
        if addresses:
            code = self.insert_addresses(code, addresses)
        if replace_unknown_addresses:
            # Replace unknown addresses with 0x0
            code = re.sub(r'\{\{\S*\}\}', '0x0', code)
        return code

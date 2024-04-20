import json
import re


class Grammer:
    nonterms = set()
    terms = set()
    start_nonterm = None
    productions = {}

    @staticmethod
    def from_json(file_path):
        grammer = Grammer()

        file = open(file_path)
        doc = json.load(file)
        
        grammer.nonterms = set(doc['nonterms'])
        grammer.terms = set(doc['terms'])
        grammer.productions = doc['productions']
        grammer.start_nonterm = doc['start_nonterm']

        return grammer
    
    @staticmethod
    def remove_left_recursion_for(nonterm, productions):
        transit_nonterm = f'{nonterm}\''
        transit_nonterm_productions = []

        new_productions = []
        for production in productions:
            if production == 'ε':
                transit_nonterm_productions.append('ε')
                new_productions.append(transit_nonterm)
                continue

            match = re.match(f'{nonterm}(.*)', production)
            if match is not None:
                transit_nonterm_productions.append(f'{match.group(1)}{transit_nonterm}')
                continue

            new_productions.append(f'{production}{transit_nonterm}')

        return nonterm, new_productions, transit_nonterm, transit_nonterm_productions

    def closure(self, nonterm, prev_nonterm):
        productions_closure = []
        for production in self.productions[nonterm]:
            match = re.match(f'{prev_nonterm}(.*)', production)
            if match is not None:
                for prev_nonterm_production in self.productions[prev_nonterm]:
                    productions_closure.append(f'{prev_nonterm_production}{match.group(1)}')
                continue
            
            productions_closure.append(production)

        return productions_closure

    def removed_left_recursion(self):
        grammer = Grammer()
        grammer.terms = self.terms
        grammer.start_nonterm = self.start_nonterm

        for _, nonterm in enumerate(reversed(sorted(self.nonterms))):
            grammer.nonterms.add(nonterm)
            grammer.productions[nonterm] = self.productions[nonterm]

            for _, prev_nonterm in enumerate(reversed(sorted(self.nonterms))):
                if  nonterm == prev_nonterm:
                    break

                _, new_productions, transit_nonterm, transit_nonterm_productions = self.remove_left_recursion_for(
                    nonterm, self.closure(nonterm, prev_nonterm)
                )
                
                if len(transit_nonterm_productions) == 0:
                    continue

                grammer.nonterms.add(transit_nonterm)
                grammer.productions.update({nonterm: new_productions})
                grammer.productions.update({transit_nonterm: transit_nonterm_productions})

        return grammer   

    def removed_unreachables(self):
        grammer = Grammer()
        grammer.start_nonterm = self.start_nonterm

        v = [set(self.start_nonterm)]

        while True:
            v.append(set(v[-1]))
            
            for symbol in self.nonterms | self.terms:
                for key in self.productions:
                    if key not in v[-2]:
                        continue
                    
                    for rhs in self.productions[key]:
                        if re.search(f'.*{re.escape(symbol)}.*', rhs):
                            v[-1].add(symbol)

            if v[-1] == v[-2]:
                break
        
        grammer.nonterms = self.nonterms & v[-1]
        grammer.terms = self.terms & v[-1]
        
        productions = {}
        for key in self.productions:
            if key in grammer.nonterms:
                productions[key] = self.productions[key]
        grammer.productions = productions

        return grammer

    def __str__(self):
        return \
            f'{{\n'\
            f'    {{{', '.join(self.nonterms)}}},\n'\
            f'    {{{', '.join(self.terms)}}},\n'\
            f'    {{\n        {',\n        '.join([f'{k} -> {'|'.join(self.productions[k])}' for k in self.productions.keys()])}\n    }},\n'\
            f'    {self.start_nonterm}\n'\
            f'}}'

def main():
    file_path = 'grammer.json'
    # file_path = input()

    grammer = Grammer.from_json(file_path)
    print(grammer, end='\n\n')
    grammer = grammer.removed_left_recursion()
    print(grammer, end='\n\n')
    grammer = grammer.removed_unreachables()
    print(grammer)

if __name__ == '__main__':
    main()
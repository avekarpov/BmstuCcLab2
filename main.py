import json
import re


class Grammer:
    _nonterms = None
    _terms = None
    _start_term = None
    _productions = None

    def by_json(self, file_path):
        file = open(file_path)
        doc = json.load(file)
        
        self._nonterms = set(doc['nonterms'])
        self._terms = set(doc['terms'])
        self._productions = doc['productions']
        self._start_nonterm = doc['start_nonterm']

        return self
    
    def remove_left_recursion(self):
        new_nonterms = set()
        new_productions = {}

        for i, nonterm in enumerate(reversed(sorted(self._nonterms))):
            new_nonterms.add(nonterm)
            new_productions.update({nonterm: self._productions[nonterm]})

            for j, prev_nonterm in enumerate(reversed(sorted(self._nonterms))):
                if j == i:
                    break
                
                nonterm_productions_closure = []
                for nonterm_productions in self._productions[nonterm]:
                    match = re.match(f'{prev_nonterm}(.*)', nonterm_productions)
                    if match is not None:
                        for prev_nonterm_productions in self._productions[prev_nonterm]:
                            nonterm_productions_closure.append(f'{prev_nonterm_productions}{match.group(1)}')
                    else:
                        nonterm_productions_closure.append(nonterm_productions)

                _, nonterm_new_productions, transit_nonterm, transit_nonterm_productions = self.remove_left_recursion_for(nonterm, nonterm_productions_closure)
                
                if len(transit_nonterm_productions) == 0:
                    continue

                new_nonterms.add(transit_nonterm)
                new_productions.update({nonterm: nonterm_new_productions})
                new_productions.update({transit_nonterm: transit_nonterm_productions})

        self._nonterms = new_nonterms
        self._productions = new_productions

        return self   

    def remove_left_recursion_for(self, nonterm, productions):
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
            else:
                new_productions.append(f'{production}{transit_nonterm}')

        return nonterm, new_productions, transit_nonterm, transit_nonterm_productions

    def remove_unreachables(self):
        vs = [set(self._start_nonterm)]

        while True:
            v = set()
            
            for symbol in self._nonterms | self._terms:
                for key in self._productions:
                    if key not in vs[-1]:
                        continue
                    
                    for rhs in self._productions[key]:
                        if re.search(f'.*{re.escape(symbol)}.*', rhs):
                            v.add(symbol)

            vs.append(vs[-1] | v)

            if vs[-1] == vs[-2]:
                break
        
        self._nonterms = self._nonterms & vs[-1]
        self._terms = self._terms & vs[-1]
        
        productions = {}
        for key in self._productions:
            if key in self._nonterms:
                productions[key] = self._productions[key]
        self._productions = productions

        return self

    def __str__(self):
        return \
            f'{{\n'\
            f'    {self._nonterms},\n'\
            f'    {self._terms},\n'\
            f'    {{\n        {',\n        '.join([f'{k} -> {'|'.join(self._productions[k])}' for k in self._productions.keys()])}\n    }},\n'\
            f'    {self._start_nonterm}\n'\
            f'}}'

def main():
    file_path = 'grammer.json'
    # file_path = input()

    grammer = Grammer().by_json(file_path)
    print(grammer, end='\n\n')
    grammer.remove_left_recursion()
    print(grammer, end='\n\n')
    grammer.remove_unreachables()
    print(grammer)

if __name__ == '__main__':
    main()
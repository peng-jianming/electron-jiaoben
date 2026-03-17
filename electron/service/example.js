'use strict';

class ExampleService {
  constructor() {
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};